from __future__ import annotations

import hashlib
import json
import re
import tomllib
import unicodedata
import urllib.parse
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from .candidates import CandidatePool
from .http import HttpClient
from .features import FeatureExtractor
from .models import KnowledgeCard, RawItem, utc_now
from .ranking import CohortRanker
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


def candidate_id(item: RawItem) -> str:
    return hashlib.sha256(identity(item).encode("utf-8")).hexdigest()[:16]


class Pipeline:
    """Deep module: callers configure paths; collection, ranking and cards stay local."""

    def __init__(
        self,
        *,
        client: HttpClient,
        summarizer: Summarizer,
        now: datetime | None = None,
        strict_summaries: bool = False,
        feature_extractor: FeatureExtractor | None = None,
        ranker: CohortRanker | None = None,
    ) -> None:
        self.client = client
        self.summarizer = summarizer
        self.now = now or utc_now()
        self.strict_summaries = strict_summaries
        self.feature_extractor = feature_extractor or FeatureExtractor()
        self.ranker = ranker or CohortRanker()

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

    def run(
        self,
        config_path: Path,
        output_path: Path,
        *,
        candidate_path: Path | None = None,
        published_path: Path | None = None,
    ) -> PipelineReport:
        config = tomllib.loads(config_path.read_text(encoding="utf-8"))
        project = config.get("project", {})
        default_lookback = int(project.get("lookback_hours", 72))
        max_age_days = int(project.get("max_age_days", 15))
        primary_window_hours = int(project.get("primary_window_hours", 48))
        edition = self.now.astimezone(timezone(timedelta(hours=8))).strftime("%Y.%m.%d")
        candidate_pool = CandidatePool(candidate_path)
        candidate_pool.seed_published_dataset(published_path or output_path)
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
                cutoff = self._cutoff(
                    lookback_hours=int(source.get("lookback_hours", default_lookback)),
                    max_age_days=max_age_days,
                )
                raw_items.extend(item for item in fetched if item.published_at >= cutoff)
            except Exception as error:  # One source must never stop the daily edition.
                errors[source["id"]] = f"{type(error).__name__}: {error}"

        unique = self._deduplicate(raw_items)
        candidate_pool.ingest([(candidate_id(item), item) for item in unique], self.now, max_age_days)
        primary, carryover = candidate_pool.selection_lanes(
            self.now,
            primary_window_hours=primary_window_hours,
            max_age_days=max_age_days,
            current_edition=edition,
        )
        primary_objects = {id(item) for item in primary}
        eligible_ranked = self.ranker.rank(primary + carryover, self.now)
        for result in eligible_ranked:
            result.breakdown["selectionLane"] = "primary" if id(result.item) in primary_objects else "carryover"
        ranked_results = (
            [result for result in eligible_ranked if id(result.item) in primary_objects]
            + [result for result in eligible_ranked if id(result.item) not in primary_objects]
        )
        source_caps = {source["id"]: int(source.get("max_daily", 3)) for source in config.get("sources", [])}
        content_caps = {key: int(value) for key, value in project.get("content_caps", {}).items()}
        content_mins = {key: int(value) for key, value in project.get("content_mins", {}).items()}
        source_mins = {key: int(value) for key, value in project.get("source_mins", {}).items()}
        selected = self._select(
            ranked_results,
            int(project.get("daily_limit", 15)),
            source_caps,
            content_caps,
            content_mins,
            source_mins,
        )
        self._validate_selection(selected, content_mins=content_mins, source_mins=source_mins)
        cards = [self._to_card(result.item, result.score, result.breakdown) for result in selected]
        payload = {
            "generatedAt": self.now.isoformat(),
            "timezone": project.get("timezone", "Asia/Singapore"),
            "edition": edition,
            "cards": [card.as_web_dict() for card in cards],
            "sourceErrors": errors,
        }
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        candidate_pool.mark_published(
            [(candidate_id(result.item), result.item) for result in selected],
            self.now,
            edition,
        )
        candidate_pool.save(self.now)
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

    @staticmethod
    def _cutoff_for(now: datetime, *, lookback_hours: int, max_age_days: int) -> datetime:
        requested = now - timedelta(hours=max(0, lookback_hours))
        hard_limit = now - timedelta(days=max(0, max_age_days))
        return max(requested, hard_limit)

    def _cutoff(self, *, lookback_hours: int, max_age_days: int) -> datetime:
        return self._cutoff_for(self.now, lookback_hours=lookback_hours, max_age_days=max_age_days)

    @staticmethod
    def _select(
        items: list[Any],
        limit: int,
        source_caps: dict[str, int],
        content_caps: dict[str, int] | None = None,
        content_mins: dict[str, int] | None = None,
        source_mins: dict[str, int] | None = None,
    ) -> list[Any]:
        selected: list[Any] = []
        selected_ids: set[int] = set()
        counts: dict[str, int] = {}
        content_counts: dict[str, int] = {}
        caps = content_caps or {}
        minimums = content_mins or {}
        required_sources = source_mins or {}

        def add(result: Any, *, enforce_content_cap: bool = True) -> bool:
            if id(result) in selected_ids or len(selected) >= limit:
                return False
            item = result.item
            cap = source_caps.get(item.source_id, 3)
            if counts.get(item.source_id, 0) >= cap:
                return False
            content_cap = caps.get(item.content_type)
            if enforce_content_cap and content_cap is not None and content_counts.get(item.content_type, 0) >= content_cap:
                return False
            selected.append(result)
            selected_ids.add(id(result))
            counts[item.source_id] = counts.get(item.source_id, 0) + 1
            content_counts[item.content_type] = content_counts.get(item.content_type, 0) + 1
            return True

        for source_id, required in required_sources.items():
            for result in items:
                if counts.get(source_id, 0) >= required:
                    break
                if result.item.source_id == source_id:
                    add(result)

        for content_type, required in minimums.items():
            for result in items:
                if content_counts.get(content_type, 0) >= required:
                    break
                if result.item.content_type == content_type:
                    add(result)

        for result in items:
            add(result)
            if len(selected) >= limit:
                break

        if len(selected) < limit:
            for result in items:
                add(result, enforce_content_cap=False)
                if len(selected) >= limit:
                    break
        return sorted(selected, key=lambda result: result.score, reverse=True)

    @staticmethod
    def _validate_selection(
        selected: list[Any],
        *,
        content_mins: dict[str, int],
        source_mins: dict[str, int],
    ) -> None:
        content_counts: dict[str, int] = {}
        source_counts: dict[str, int] = {}
        for result in selected:
            item = result.item
            content_counts[item.content_type] = content_counts.get(item.content_type, 0) + 1
            source_counts[item.source_id] = source_counts.get(item.source_id, 0) + 1
        missing = [
            f"{content_type}:{required - content_counts.get(content_type, 0)}"
            for content_type, required in content_mins.items()
            if content_counts.get(content_type, 0) < required
        ]
        missing.extend(
            f"source={source_id}:{required - source_counts.get(source_id, 0)}"
            for source_id, required in source_mins.items()
            if source_counts.get(source_id, 0) < required
        )
        if missing:
            raise RuntimeError("required Edition coverage unavailable: " + ", ".join(missing))

    def _to_card(self, item: RawItem, score: float, score_breakdown: dict[str, object] | None = None) -> KnowledgeCard:
        fallback = SourceSummary()
        try:
            result = self.summarizer.summarize(item)
        except Exception as error:
            if self.strict_summaries:
                raise RuntimeError(f"AI summary failed for {item.source_name}: {item.title}") from error
            result = fallback.summarize(item)
        slug = slug_for(item)
        return KnowledgeCard(
            id=candidate_id(item),
            slug=slug,
            domain=item.domain,
            content_type=item.content_type,
            source_name=item.source_name,
            source_group=item.source_group,
            original_title=item.title,
            title=result.title,
            description=result.description,
            summary=result.summary,
            key_points=result.key_points,
            why_it_matters=result.why_it_matters,
            limitations=result.limitations,
            title_en=result.title_en,
            description_en=result.description_en,
            summary_en=result.summary_en,
            key_points_en=result.key_points_en,
            why_it_matters_en=result.why_it_matters_en,
            limitations_en=result.limitations_en,
            original_url=canonical_url(item.url),
            published_at=item.published_at,
            retrieved_at=item.retrieved_at,
            tags=result.tags,
            features=[feature.as_dict() for feature in self.feature_extractor.extract(item)],
            score=score,
            score_breakdown=score_breakdown or {},
            ai_generated=result.ai_generated,
            summary_provider=result.provider,
            summary_model=result.model,
            discovered_by=item.discovered_by,
        )
