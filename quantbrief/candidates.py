from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from .models import RawItem


@dataclass(slots=True)
class CandidateRecord:
    candidate_id: str
    item: RawItem
    first_seen_at: datetime
    last_seen_at: datetime


class CandidatePool:
    """Durable unpublished candidates plus cross-Edition publication memory."""

    VERSION = 1

    def __init__(self, path: Path | None = None) -> None:
        self.path = path
        self.candidates: dict[str, CandidateRecord] = {}
        self.published: dict[str, dict[str, Any]] = {}
        if path and path.exists():
            self._load(path)

    def seed_published_dataset(self, path: Path) -> None:
        if not path.exists():
            return
        try:
            dataset = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return
        for card in dataset.get("cards", []):
            candidate_id = str(card.get("id", "")).strip()
            if not candidate_id or candidate_id in self.published:
                continue
            breakdown = card.get("scoreBreakdown", {})
            self.published[candidate_id] = {
                "publishedAt": card.get("retrievedAt") or card.get("publishedAt") or dataset.get("generatedAt"),
                "edition": dataset.get("edition"),
                "sourceId": "github-trending-daily"
                if any(feature.get("id") == "ranking:github-trending-daily" for feature in card.get("features", []))
                else None,
                "metrics": breakdown.get("sourceMetrics", {}),
            }

    def ingest(self, items: list[tuple[str, RawItem]], now: datetime, max_age_days: int) -> None:
        cutoff = now - timedelta(days=max_age_days)
        for candidate_id, item in items:
            if item.published_at < cutoff:
                continue
            existing = self.candidates.get(candidate_id)
            self.candidates[candidate_id] = CandidateRecord(
                candidate_id=candidate_id,
                item=item,
                first_seen_at=existing.first_seen_at if existing else now,
                last_seen_at=now,
            )
        self.candidates = {
            candidate_id: record
            for candidate_id, record in self.candidates.items()
            if record.item.published_at >= cutoff
        }

    def selection_lanes(
        self,
        now: datetime,
        *,
        primary_window_hours: int,
        max_age_days: int,
        current_edition: str,
    ) -> tuple[list[RawItem], list[RawItem]]:
        primary_cutoff = now - timedelta(hours=primary_window_hours)
        oldest = now - timedelta(days=max_age_days)
        primary: list[RawItem] = []
        carryover: list[RawItem] = []
        for candidate_id, record in self.candidates.items():
            item = record.item
            if item.published_at < oldest or not self._eligible(candidate_id, item, current_edition):
                continue
            target = primary if item.published_at >= primary_cutoff else carryover
            target.append(item)
        return primary, carryover

    def mark_published(self, items: list[tuple[str, RawItem]], now: datetime, edition: str) -> None:
        for candidate_id, item in items:
            self.published[candidate_id] = {
                "publishedAt": now.isoformat(),
                "edition": edition,
                "sourceId": item.source_id,
                "metrics": dict(item.metrics),
            }

    def save(self, now: datetime) -> None:
        if self.path is None:
            return
        payload = {
            "version": self.VERSION,
            "updatedAt": now.isoformat(),
            "candidates": [self._record_dict(record) for record in self.candidates.values()],
            "published": self.published,
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def _eligible(self, candidate_id: str, item: RawItem, current_edition: str) -> bool:
        published = self.published.get(candidate_id)
        if not published:
            return True
        if published.get("edition") == current_edition:
            return True
        if item.source_id != "github-trending-daily":
            return False
        previous = published.get("metrics", {})
        current_delta = float(item.metrics.get("stars_delta_1d", 0.0))
        previous_delta = float(previous.get("stars_delta_1d", 0.0))
        current_stars = float(item.metrics.get("stars", 0.0))
        previous_stars = float(previous.get("stars", 0.0))
        delta_anomaly = current_delta >= 500.0 and current_delta >= max(1.0, previous_delta) * 2.0
        total_growth = current_stars - previous_stars
        growth_anomaly = total_growth >= max(1000.0, previous_stars * 0.25)
        return delta_anomaly or growth_anomaly

    def _load(self, path: Path) -> None:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return
        if payload.get("version") != self.VERSION:
            return
        self.published = dict(payload.get("published", {}))
        for row in payload.get("candidates", []):
            try:
                record = self._record_from_dict(row)
            except (KeyError, TypeError, ValueError):
                continue
            self.candidates[record.candidate_id] = record

    @staticmethod
    def _record_dict(record: CandidateRecord) -> dict[str, Any]:
        item = asdict(record.item)
        item["published_at"] = record.item.published_at.isoformat()
        item["retrieved_at"] = record.item.retrieved_at.isoformat()
        return {
            "candidateId": record.candidate_id,
            "firstSeenAt": record.first_seen_at.isoformat(),
            "lastSeenAt": record.last_seen_at.isoformat(),
            "item": item,
        }

    @staticmethod
    def _record_from_dict(row: dict[str, Any]) -> CandidateRecord:
        item = dict(row["item"])
        item["published_at"] = datetime.fromisoformat(item["published_at"])
        item["retrieved_at"] = datetime.fromisoformat(item["retrieved_at"])
        return CandidateRecord(
            candidate_id=str(row["candidateId"]),
            item=RawItem(**item),
            first_seen_at=datetime.fromisoformat(row["firstSeenAt"]),
            last_seen_at=datetime.fromisoformat(row["lastSeenAt"]),
        )
