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
    return RawItem(
        source_id=source["id"],
        source_name=source["name"],
        source_group=source["group"],
        domain=source["domain"],
        retrieved_at=now,
        priority=float(source.get("priority", 1.0)),
        tags=tags,
        discovered_by=[source["name"]],
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
                items.append(_base_item(
                    source, now,
                    title=clean_html(entry.findtext("{*}title")),
                    url=link,
                    summary=clean_html(entry.findtext("{*}summary") or entry.findtext("{*}content")),
                    published_at=parse_date(entry.findtext("{*}published") or entry.findtext("{*}updated"), now),
                    authors=[author for author in authors if author],
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
            ))
        return items


class GitHubAdapter:
    def fetch(self, source: dict[str, Any], client: HttpClient, now: datetime) -> list[RawItem]:
        repo = source["repo"]
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
            ))
        return items


ADAPTERS: dict[str, SourceAdapter] = {
    "rss": RssAdapter(),
    "huggingface": HuggingFaceAdapter(),
    "github": GitHubAdapter(),
}
