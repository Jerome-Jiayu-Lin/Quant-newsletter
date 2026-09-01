from __future__ import annotations

import email.utils
import json
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from html.parser import HTMLParser
from typing import Any, Protocol

from .http import HttpClient
from .models import RawItem, utc_now


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def clean_html(value: str | None) -> str:
    if not value:
        return ""
    parser = _TextExtractor()
    parser.feed(value)
    cleaned = re.sub(r"\s+", " ", " ".join(parser.parts)).strip()
    return re.sub(r"^arXiv:\S+\s+Announce Type:\s*\S+\s+Abstract:\s*", "", cleaned, flags=re.I)


def parse_date(value: str | None, fallback: datetime) -> datetime:
    if not value:
        return fallback
    try:
        parsed = email.utils.parsedate_to_datetime(value)
        return parsed.astimezone(timezone.utc)
    except (TypeError, ValueError):
        pass
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.astimezone(timezone.utc)
    except ValueError:
        return fallback


class SourceAdapter(Protocol):
    def fetch(self, source: dict[str, Any], client: HttpClient, now: datetime) -> list[RawItem]: ...


def _base_item(source: dict[str, Any], now: datetime, **values: Any) -> RawItem:
    tags = values.pop("tags", list(source.get("tags", [])))
    content_type = values.pop("content_type", source.get("content_type"))
    if not content_type:
        content_type = {
            "论文": "paper",
            "开源项目": "repository",
            "视频": "video",
        }.get(source.get("group"), "article")
    return RawItem(
        source_id=source["id"],
        source_name=source["name"],
        source_group=source["group"],
        domain=source["domain"],
        retrieved_at=now,
        priority=float(source.get("priority", 1.0)),
        tags=tags,
        discovered_by=[source["name"]],
        content_type=content_type,
        **values,
    )


class RssAdapter:
    def fetch(self, source: dict[str, Any], client: HttpClient, now: datetime) -> list[RawItem]:
        response = client.get(source["url"], accept="application/atom+xml, application/rss+xml, application/xml, text/xml")
        if response.status == 304:
            return []
        root = ET.fromstring(response.body)
        items: list[RawItem] = []
        if root.tag.endswith("feed"):
            for entry in root.findall("{*}entry"):
                link_node = next((node for node in entry.findall("{*}link") if node.attrib.get("rel", "alternate") == "alternate"), None)
                link = (link_node.attrib.get("href", "") if link_node is not None else "").strip()
                if not link:
                    continue
                authors = [clean_html(node.findtext("{*}name")) for node in entry.findall("{*}author")]
                media_description = entry.findtext("{*}group/{*}description")
                statistics = entry.find("{*}group/{*}community/{*}statistics")
                metrics: dict[str, float] = {}
                if statistics is not None and statistics.attrib.get("views"):
                    metrics["views"] = float(statistics.attrib["views"])
                items.append(_base_item(
                    source, now,
                    title=clean_html(entry.findtext("{*}title")),
                    url=link,
                    summary=clean_html(entry.findtext("{*}summary") or entry.findtext("{*}content") or media_description),
                    published_at=parse_date(entry.findtext("{*}published") or entry.findtext("{*}updated"), now),
                    authors=[author for author in authors if author],
                    metrics=metrics,
                ))
        else:
            for entry in root.findall(".//item"):
                link = (entry.findtext("link") or "").strip()
                if not link:
                    continue
                items.append(_base_item(
                    source, now,
                    title=clean_html(entry.findtext("title")),
                    url=link,
                    summary=clean_html(entry.findtext("description") or entry.findtext("{*}encoded")),
                    published_at=parse_date(entry.findtext("pubDate") or entry.findtext("{*}date"), now),
                    authors=[clean_html(entry.findtext("{*}creator"))] if entry.findtext("{*}creator") else [],
                ))
        return items


class HuggingFaceAdapter:
    def fetch(self, source: dict[str, Any], client: HttpClient, now: datetime) -> list[RawItem]:
        response = client.get(source["url"], accept="application/json")
        if response.status == 304:
            return []
        payload = json.loads(response.body)
        rows = payload if isinstance(payload, list) else payload.get("items", [])
        items: list[RawItem] = []
        for row in rows:
            paper = row.get("paper", row)
            paper_id = str(paper.get("id") or paper.get("paperId") or "").strip()
            if not paper_id:
                continue
            authors = paper.get("authors", [])
            items.append(_base_item(
                source, now,
                title=clean_html(paper.get("title")),
                url=f"https://arxiv.org/abs/{paper_id}",
                summary=clean_html(paper.get("summary") or paper.get("ai_summary")),
                published_at=parse_date(row.get("publishedAt") or paper.get("publishedAt"), now),
                authors=[author.get("name", "") if isinstance(author, dict) else str(author) for author in authors],
                tags=list(source.get("tags", [])) + (["热门论文"] if row.get("numUpvotes", 0) else []),
                content_type="paper",
                metrics={"upvotes": float(row.get("numUpvotes", 0))},
            ))
        return items


class GitHubAdapter:
    def fetch(self, source: dict[str, Any], client: HttpClient, now: datetime) -> list[RawItem]:
        repo = source["repo"]
        repository_response = client.get(
            f"https://api.github.com/repos/{repo}",
            accept="application/vnd.github+json",
            headers=client.github_headers(),
        )
        repository = json.loads(repository_response.body) if repository_response.status != 304 else {}
        metrics = {}
        if "stargazers_count" in repository:
            metrics["stars"] = float(repository["stargazers_count"])
        if "forks_count" in repository:
            metrics["forks"] = float(repository["forks_count"])
        if "open_issues_count" in repository:
            metrics["open_issues"] = float(repository["open_issues_count"])
        if repository.get("created_at"):
            created_at = parse_date(repository["created_at"], now)
            metrics["metric_age_days"] = max(1.0, (now - created_at).total_seconds() / 86400)
        url = f"https://api.github.com/repos/{repo}/releases?per_page=5"
        response = client.get(url, accept="application/vnd.github+json", headers=client.github_headers())
        if response.status == 304:
            return []
        items: list[RawItem] = []
        for release in json.loads(response.body):
            if release.get("draft"):
                continue
            tag = release.get("tag_name") or release.get("name") or "release"
            items.append(_base_item(
                source, now,
                title=f"{repo} {tag}",
                url=release.get("html_url") or f"https://github.com/{repo}/releases",
                summary=clean_html(release.get("body"))[:5000],
                published_at=parse_date(release.get("published_at") or release.get("created_at"), now),
                authors=[(release.get("author") or {}).get("login", "")],
                tags=list(source.get("tags", [])) + ["Release"],
                content_type="repository",
                metrics=metrics,
            ))
        return items


class GitHubTrendingAdapter:
    """GitHub's ordered daily list; publication history chooses the first three eligible repositories."""

    def fetch(self, source: dict[str, Any], client: HttpClient, now: datetime) -> list[RawItem]:
        response = client.get(source["url"], accept="text/html")
        if response.status == 304:
            return []
        html = response.body.decode("utf-8", errors="replace")
        items: list[RawItem] = []
        for rank, article in enumerate(re.findall(r"<article\b[\s\S]*?</article>", html, re.I), start=1):
            if rank > int(source.get("scan_limit", 25)):
                break
            repository_match = re.search(r"<h2\b[\s\S]*?<a[^>]+href=[\"']/([^\"']+)[\"']", article, re.I)
            if not repository_match:
                continue
            repository = clean_html(repository_match.group(1)).replace(" ", "")
            description_match = re.search(r"<p[^>]*class=[\"'][^\"']*col-9[^\"']*[\"'][^>]*>([\s\S]*?)</p>", article, re.I)
            description = clean_html(description_match.group(1)) if description_match else ""
            language_match = re.search(r"itemprop=[\"']programmingLanguage[\"'][^>]*>([\s\S]*?)</span>", article, re.I)
            language = clean_html(language_match.group(1)) if language_match else ""
            stars_match = re.search(r"href=[\"']/[^\"']+/stargazers[\"'][^>]*>([\s\S]*?)</a>", article, re.I)
            stars_today_match = re.search(r"([\d,]+)\s+stars?\s+today", clean_html(article), re.I)
            stars = self._number(clean_html(stars_match.group(1))) if stars_match else 0.0
            stars_today = self._number(stars_today_match.group(1)) if stars_today_match else 0.0
            text = f"{repository} {description} {language}".casefold()
            domain = self._domain(text)
            items.append(
                _base_item(
                    {**source, "domain": domain},
                    now,
                    title=repository,
                    url=f"https://github.com/{repository}",
                    summary=description or f"GitHub daily trending repository written in {language or 'an unspecified language'}.",
                    published_at=now,
                    tags=list(source.get("tags", [])) + ([language] if language else []),
                    content_type="repository",
                    metrics={
                        "trending_rank": float(rank),
                        "trending_rank_score": max(0.0, 100.0 - float(rank)),
                        "stars": stars,
                        "stars_delta_1d": stars_today,
                        "metric_age_days": 1.0,
                    },
                )
            )
        return items

    @staticmethod
    def _number(value: str) -> float:
        cleaned = re.sub(r"[^\d.]", "", value)
        return float(cleaned) if cleaned else 0.0

    @staticmethod
    def _domain(text: str) -> str:
        quant = any(term in text for term in ("quant", "finance", "trading", "portfolio", "market"))
        ai = any(term in text for term in ("ai", "llm", "agent", "machine learning", "deep learning"))
        if quant and ai:
            return "AI × 量化"
        if quant:
            return "量化研究"
        if ai or "skill" in text:
            return "AI 工具"
        return "开源工程"


ADAPTERS: dict[str, SourceAdapter] = {
    "rss": RssAdapter(),
    "huggingface": HuggingFaceAdapter(),
    "github": GitHubAdapter(),
    "github_trending": GitHubTrendingAdapter(),
}
