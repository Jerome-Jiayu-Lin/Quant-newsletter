from __future__ import annotations

import hashlib
import json
import math
import re
import tomllib
import unicodedata
import urllib.parse
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from .http import HttpClient
from .models import KnowledgeCard, RawItem, utc_now
from .sources import ADAPTERS
from .summarize import SourceSummary, Summarizer, configured_summarizer


TRACKING_PARAMS = {"fbclid", "gclid", "mc_cid", "mc_eid", "ref", "source"}


@dataclass(slots=True)
class PipelineReport:
    fetched: int
    deduplicated: int
    selected: int
    source_errors: dict[str, str]
    output_path: Path


def canonical_url(value: str) -> str:
    parsed = urllib.parse.urlsplit(value.strip())
    query = [
        (key, item)
        for key, item in urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
        if not key.lower().startswith("utm_") and key.lower() not in TRACKING_PARAMS
    ]
    path = parsed.path.rstrip("/") or "/"
    return urllib.parse.urlunsplit((parsed.scheme.lower(), parsed.netloc.lower(), path, urllib.parse.urlencode(query), ""))


def title_fingerprint(title: str) -> str:
    normalized = unicodedata.normalize("NFKC", title).casefold()
    return re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "", normalized)


def identity(item: RawItem) -> str:
    arxiv = re.search(r"arxiv\.org/(?:abs|pdf)/([^/?#]+)", item.url, re.I)
    if arxiv:
        return f"arxiv:{re.sub(r'v\d+$', '', arxiv.group(1))}"
    return canonical_url(item.url) or title_fingerprint(item.title)


def slug_for(item: RawItem) -> str:
    digest = hashlib.sha256(identity(item).encode("utf-8")).hexdigest()[:10]
    readable = re.sub(r"[^a-z0-9]+", "-", item.title.casefold()).strip("-")[:48]
    return f"{readable or 'signal'}-{digest}"


class Pipeline:
    """Deep module: callers configure paths; collection, ranking and cards stay local."""

    def __init__(
        self,
        *,
        client: HttpClient,
        summarizer: Summarizer,
        now: datetime | None = None,
        strict_summaries: bool = False,
    ) -> None:
        self.client = client
        self.summarizer = summarizer
        self.now = now or utc_now()
        self.strict_summaries = strict_summaries

    @classmethod
    def configured(
        cls,
        state_path: Path,
        now: datetime | None = None,
        *,
        require_ai: bool = False,
    ) -> "Pipeline":
        return cls(
            client=HttpClient(state_path),
            summarizer=configured_summarizer(require_ai=require_ai),
            now=now,
            strict_summaries=require_ai,
        )

    def run(self, config_path: Path, output_path: Path) -> PipelineReport:
        config = tomllib.loads(config_path.read_text(encoding="utf-8"))
        project = config.get("project", {})
        default_lookback = int(project.get("lookback_hours", 72))
        raw_items: list[RawItem] = []
        errors: dict[str, str] = {}
        for source in config.get("sources", []):
            if not source.get("enabled", True):
                continue
            adapter = ADAPTERS.get(source["kind"])
            if adapter is None:
                errors[source["id"]] = f"unknown source kind: {source['kind']}"
                continue
            try:
                fetched = adapter.fetch(source, self.client, self.now)
                cutoff = self.now - timedelta(hours=int(source.get("lookback_hours", default_lookback)))
                raw_items.extend(item for item in fetched if item.published_at >= cutoff)
            except Exception as error:  # One source must never stop the daily edition.
                errors[source["id"]] = f"{type(error).__name__}: {error}"

        unique = self._deduplicate(raw_items)
        ranked = sorted(unique, key=self._score, reverse=True)
        source_caps = {source["id"]: int(source.get("max_daily", 3)) for source in config.get("sources", [])}
        selected = self._select(ranked, int(project.get("daily_limit", 15)), source_caps)
        cards = [self._to_card(item, self._score(item)) for item in selected]
        payload = {
            "generatedAt": self.now.isoformat(),
            "timezone": project.get("timezone", "Asia/Singapore"),
            "edition": self.now.astimezone(timezone(timedelta(hours=8))).strftime("%Y.%m.%d"),
            "cards": [card.as_web_dict() for card in cards],
            "sourceErrors": errors,
        }
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        self.client.save()
        return PipelineReport(len(raw_items), len(unique), len(cards), errors, output_path)

    def _deduplicate(self, items: list[RawItem]) -> list[RawItem]:
        merged: dict[str, RawItem] = {}
        titles: dict[str, str] = {}
        for item in items:
            key = identity(item)
            title_key = title_fingerprint(item.title)
            existing_key = key if key in merged else titles.get(title_key)
            if existing_key and existing_key in merged:
                existing = merged[existing_key]
                existing.discovered_by = sorted(set(existing.discovered_by + item.discovered_by))
                if item.priority > existing.priority:
                    item.discovered_by = existing.discovered_by
                    merged[existing_key] = item
                continue
            merged[key] = item
            if title_key:
                titles[title_key] = key
        return list(merged.values())

    def _score(self, item: RawItem) -> float:
        age_hours = max(0.0, (self.now - item.published_at).total_seconds() / 3600)
        recency = max(0.0, 22.0 - math.log2(age_hours + 1) * 4.5)
        domain = {"量化研究": 24, "AI × 量化": 21, "开源工程": 17, "AI 工具": 12}.get(item.domain, 8)
        evidence = 8 if any(tag in {"论文", "Release", "机构研究"} for tag in item.tags) else 3
        text = f"{item.title} {item.summary}".casefold()
        useful_terms = {
            "backtest", "trading", "portfolio", "factor", "alpha", "market making", "order book",
            "execution", "volatility", "risk", "hedg", "asset pricing", "return predict", "causal",
            "agent", "time series", "forecast", "reinforcement learning", "evaluation", "benchmark",
            "回测", "交易", "组合", "因子", "风险", "波动", "预测", "智能体",
        }
        topic_bonus = min(18, sum(3 for term in useful_terms if term in text))
        return round(item.priority * 30 + recency + domain + evidence + topic_bonus, 2)

    @staticmethod
    def _select(items: list[RawItem], limit: int, source_caps: dict[str, int]) -> list[RawItem]:
        selected: list[RawItem] = []
        counts: dict[str, int] = {}
        for item in items:
            cap = source_caps.get(item.source_id, 3)
            if counts.get(item.source_id, 0) >= cap:
                continue
            selected.append(item)
            counts[item.source_id] = counts.get(item.source_id, 0) + 1
            if len(selected) >= limit:
                break
        return selected

    def _to_card(self, item: RawItem, score: float) -> KnowledgeCard:
        fallback = SourceSummary()
        try:
            result = self.summarizer.summarize(item)
        except Exception as error:
            if self.strict_summaries:
                raise RuntimeError(f"AI summary failed for {item.source_name}: {item.title}") from error
            result = fallback.summarize(item)
        slug = slug_for(item)
        return KnowledgeCard(
            id=hashlib.sha256(identity(item).encode("utf-8")).hexdigest()[:16],
            slug=slug,
            domain=item.domain,
            source_name=item.source_name,
            source_group=item.source_group,
            original_title=item.title,
            title=result.title,
            description=result.description,
            summary=result.summary,
            key_points=result.key_points,
            why_it_matters=result.why_it_matters,
            limitations=result.limitations,
            original_url=canonical_url(item.url),
            published_at=item.published_at,
            retrieved_at=item.retrieved_at,
            tags=result.tags,
            score=score,
            ai_generated=result.ai_generated,
            summary_provider=result.provider,
            summary_model=result.model,
            discovered_by=item.discovered_by,
        )
