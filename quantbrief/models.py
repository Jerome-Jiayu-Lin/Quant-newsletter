from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(slots=True)
class RawItem:
    source_id: str
    source_name: str
    source_group: str
    domain: str
    title: str
    url: str
    summary: str
    published_at: datetime
    retrieved_at: datetime
    authors: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    priority: float = 1.0
    discovered_by: list[str] = field(default_factory=list)
    content_type: str = "article"
    metrics: dict[str, float] = field(default_factory=dict)


@dataclass(slots=True)
class KnowledgeCard:
    id: str
    slug: str
    domain: str
    source_name: str
    source_group: str
    original_title: str
    title: str
    description: str
    summary: str
    key_points: list[str]
    why_it_matters: str
    limitations: str
    title_en: str
    description_en: str
    summary_en: str
    key_points_en: list[str]
    why_it_matters_en: str
    limitations_en: str
    original_url: str
    published_at: datetime
    retrieved_at: datetime
    tags: list[str]
    features: list[dict[str, Any]]
    score: float
    score_breakdown: dict[str, Any]
    ai_generated: bool
    summary_provider: str
    summary_model: str | None
    discovered_by: list[str]

    def as_web_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["publishedAt"] = self.published_at.isoformat()
        payload["retrievedAt"] = self.retrieved_at.isoformat()
        payload["sourceName"] = payload.pop("source_name")
        payload["sourceGroup"] = payload.pop("source_group")
        payload["originalTitle"] = payload.pop("original_title")
        payload["originalUrl"] = payload.pop("original_url")
        payload["keyPoints"] = payload.pop("key_points")
        payload["whyItMatters"] = payload.pop("why_it_matters")
        payload["titleEn"] = payload.pop("title_en")
        payload["descriptionEn"] = payload.pop("description_en")
        payload["summaryEn"] = payload.pop("summary_en")
        payload["keyPointsEn"] = payload.pop("key_points_en")
        payload["whyItMattersEn"] = payload.pop("why_it_matters_en")
        payload["limitationsEn"] = payload.pop("limitations_en")
        payload["aiGenerated"] = payload.pop("ai_generated")
        payload["summaryProvider"] = payload.pop("summary_provider")
        payload["summaryModel"] = payload.pop("summary_model")
        payload["scoreBreakdown"] = payload.pop("score_breakdown")
        payload["discoveredBy"] = payload.pop("discovered_by")
        payload.pop("published_at")
        payload.pop("retrieved_at")
        return payload
