"""Provider-independent public publication contracts.

This module owns the versioned public JSON shapes. Provider adapters may transport
these dictionaries, but they must not add fields or weaken validation.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from typing import Any, Mapping


PUBLIC_SCHEMA_VERSION = 1
CARD_ID_PATTERN = re.compile(r"^[0-9a-f]{16}$")
PUBLIC_EXPORT_FIELDS = frozenset({"schemaVersion", "generatedAt", "timezone", "edition", "cards"})
PUBLIC_CARD_FIELDS = frozenset(
    {
        "id", "slug", "domain", "contentType", "sourceName", "sourceGroup",
        "originalTitle", "title", "description", "summary", "keyPoints",
        "whyItMatters", "limitations", "titleEn", "descriptionEn", "summaryEn",
        "keyPointsEn", "whyItMattersEn", "limitationsEn", "originalUrl",
        "publishedAt", "retrievedAt", "tags", "tagsEn", "features", "score",
        "scoreBreakdown", "aiGenerated", "summaryProvider", "summaryModel",
        "discoveredBy",
    }
)


def _edition_date(value: str) -> date:
    normalized = value.replace(".", "-")
    try:
        parsed = date.fromisoformat(normalized)
    except ValueError as error:
        raise ValueError(f"invalid Singapore Edition date: {value!r}") from error
    if normalized != parsed.isoformat():
        raise ValueError(f"invalid Singapore Edition date: {value!r}")
    return parsed


def edition_object_key(edition: str) -> str:
    parsed = _edition_date(edition)
    return f"editions/v1/{parsed:%Y/%m/%Y-%m-%d}/quant-brief-edition.json"


def receipt_object_key(edition: str, export_hash: str) -> str:
    parsed = _edition_date(edition)
    if not re.fullmatch(r"[0-9a-f]{64}", export_hash):
        raise ValueError("public export hash must be a lowercase SHA-256 hex digest")
    return f"publication-receipts/{parsed:%Y/%m/%Y-%m-%d}/{export_hash}.json"


def sanitize_public_export(snapshot: Mapping[str, Any]) -> dict[str, Any]:
    """Copy only the explicit public allowlist and reject unstable Card identities."""
    missing = {"generatedAt", "timezone", "edition", "cards"} - snapshot.keys()
    if missing:
        raise ValueError(f"Edition Snapshot missing public fields: {', '.join(sorted(missing))}")
    _edition_date(str(snapshot["edition"]))
    if not isinstance(snapshot["cards"], list) or not snapshot["cards"]:
        raise ValueError("Edition Snapshot must contain at least one Knowledge Card")

    cards: list[dict[str, Any]] = []
    for position, value in enumerate(snapshot["cards"]):
        if not isinstance(value, Mapping):
            raise ValueError(f"Knowledge Card {position} must be an object")
        missing_card_fields = PUBLIC_CARD_FIELDS - value.keys()
        if missing_card_fields:
            raise ValueError(
                f"Knowledge Card {position} missing public fields: {', '.join(sorted(missing_card_fields))}"
            )
        if not CARD_ID_PATTERN.fullmatch(str(value["id"])):
            raise ValueError(f"Knowledge Card {position} has an invalid stable id")
        cards.append({field: value[field] for field in PUBLIC_CARD_FIELDS})

    return {
        "schemaVersion": PUBLIC_SCHEMA_VERSION,
        "generatedAt": snapshot["generatedAt"],
        "timezone": snapshot["timezone"],
        "edition": _edition_date(str(snapshot["edition"])).isoformat(),
        "cards": cards,
    }


@dataclass(frozen=True, slots=True)
class HistoryEntry:
    edition: str
    object_key: str
    export_hash: str
    published_at: str
    card_count: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "edition": self.edition,
            "objectKey": self.object_key,
            "exportHash": self.export_hash,
            "publishedAt": self.published_at,
            "cardCount": self.card_count,
        }


@dataclass(frozen=True, slots=True)
class PublicationReceipt:
    edition: str
    canonical_snapshot_hash: str
    public_export_hash: str
    edition_object_key: str
    index_object_key: str
    receipt_object_key: str
    prior_index_hash: str | None
    resulting_index_hash: str
    deployment_identifier: str | None
    outcome: str
    published_at: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "schemaVersion": PUBLIC_SCHEMA_VERSION,
            "edition": self.edition,
            "canonicalSnapshotHash": self.canonical_snapshot_hash,
            "publicExportHash": self.public_export_hash,
            "editionObjectKey": self.edition_object_key,
            "indexObjectKey": self.index_object_key,
            "receiptObjectKey": self.receipt_object_key,
            "priorIndexHash": self.prior_index_hash,
            "resultingIndexHash": self.resulting_index_hash,
            "deploymentIdentifier": self.deployment_identifier,
            "outcome": self.outcome,
            "publishedAt": self.published_at,
        }


def history_index(entries: list[HistoryEntry], generated_at: str) -> dict[str, Any]:
    ordered = sorted(entries, key=lambda entry: _edition_date(entry.edition), reverse=True)
    if len({entry.edition for entry in ordered}) != len(ordered):
        raise ValueError("history index cannot contain duplicate Editions")
    return {
        "schemaVersion": PUBLIC_SCHEMA_VERSION,
        "generatedAt": generated_at,
        "latestEdition": ordered[0].edition if ordered else None,
        "editions": [entry.as_dict() for entry in ordered],
    }
