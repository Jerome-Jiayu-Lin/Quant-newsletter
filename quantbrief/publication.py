"""Provider-independent public publication contracts.

This module owns the versioned public JSON shapes. Provider adapters may transport
these dictionaries, but they must not add fields or weaken validation.
"""

from __future__ import annotations

import re
import hashlib
import json
from dataclasses import dataclass
from datetime import date
from typing import Any, Mapping, Protocol


PUBLIC_SCHEMA_VERSION = 1
HISTORY_INDEX_KEY = "editions/v1/index.json"
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


@dataclass(frozen=True, slots=True)
class StoredObject:
    body: bytes
    version: str


class ObjectStorage(Protocol):
    """Minimum conditional object-store behavior required by the publisher."""

    def read(self, key: str) -> StoredObject | None: ...

    def write(self, key: str, body: bytes, expected_version: str | None) -> StoredObject: ...


class StorageConflict(RuntimeError):
    """The object changed after it was read or an expected-absent key exists."""


class StalePublicationError(RuntimeError):
    """Another publisher won the conditional update."""


def _json_bytes(value: Mapping[str, Any]) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def _sha256(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def _parse_index(stored: StoredObject | None) -> tuple[list[HistoryEntry], str | None]:
    if stored is None:
        return [], None
    try:
        value = json.loads(stored.body)
        if value.get("schemaVersion") != PUBLIC_SCHEMA_VERSION or not isinstance(value.get("editions"), list):
            raise ValueError("unsupported history index schema")
        entries = [
            HistoryEntry(
                edition=entry["edition"], object_key=entry["objectKey"],
                export_hash=entry["exportHash"], published_at=entry["publishedAt"],
                card_count=entry["cardCount"],
            )
            for entry in value["editions"]
        ]
        history_index(entries, str(value["generatedAt"]))
        return entries, stored.version
    except (KeyError, TypeError, json.JSONDecodeError) as error:
        raise ValueError("malformed remote history index") from error


class Publisher:
    """Publish one Edition through a conditional, provider-independent object store."""

    def __init__(self, storage: ObjectStorage) -> None:
        self.storage = storage

    def publish(
        self,
        snapshot: Mapping[str, Any],
        *,
        published_at: str,
        deployment_identifier: str | None = None,
    ) -> PublicationReceipt:
        canonical_snapshot = _json_bytes(snapshot)
        canonical_snapshot_hash = _sha256(canonical_snapshot)
        export = sanitize_public_export(snapshot)
        export_body = _json_bytes(export)
        export_hash = _sha256(export_body)
        edition = str(export["edition"])
        edition_key = edition_object_key(edition)
        receipt_key = receipt_object_key(edition, export_hash)

        stored_index = self.storage.read(HISTORY_INDEX_KEY)
        entries, index_version = _parse_index(stored_index)
        prior_index_hash = _sha256(stored_index.body) if stored_index else None
        previous = next((entry for entry in entries if entry.edition == edition), None)
        stored_edition = self.storage.read(edition_key)

        if previous and previous.export_hash == export_hash:
            if stored_edition is None or _sha256(stored_edition.body) != export_hash:
                raise ValueError("history index references a missing or invalid Edition object")
            resulting_index_hash = prior_index_hash or _sha256(_json_bytes(history_index(entries, published_at)))
            return self._receipt(
                edition, canonical_snapshot_hash, export_hash, edition_key, receipt_key,
                prior_index_hash, resulting_index_hash, deployment_identifier, "unchanged", published_at,
            )

        expected_edition_version = stored_edition.version if stored_edition else None
        try:
            self.storage.write(edition_key, export_body, expected_edition_version)
        except StorageConflict as error:
            raise StalePublicationError("Edition object changed during publication") from error
        verified = self.storage.read(edition_key)
        if verified is None or _sha256(verified.body) != export_hash:
            raise RuntimeError("Edition object verification failed; history index was not changed")

        replacement = HistoryEntry(edition, edition_key, export_hash, published_at, len(export["cards"]))
        next_entries = [entry for entry in entries if entry.edition != edition] + [replacement]
        next_index_body = _json_bytes(history_index(next_entries, published_at))
        try:
            self.storage.write(HISTORY_INDEX_KEY, next_index_body, index_version)
        except StorageConflict as error:
            raise StalePublicationError("history index changed during publication") from error

        receipt = self._receipt(
            edition, canonical_snapshot_hash, export_hash, edition_key, receipt_key,
            prior_index_hash, _sha256(next_index_body), deployment_identifier,
            "updated" if previous else "published", published_at,
        )
        receipt_body = _json_bytes(receipt.as_dict())
        existing_receipt = self.storage.read(receipt_key)
        if existing_receipt is None:
            try:
                self.storage.write(receipt_key, receipt_body, None)
            except StorageConflict as error:
                raise StalePublicationError("publication receipt changed during publication") from error
        elif existing_receipt.body != receipt_body:
            raise StalePublicationError("publication receipt key already contains different evidence")
        return receipt

    @staticmethod
    def _receipt(
        edition: str, snapshot_hash: str, export_hash: str, edition_key: str,
        receipt_key: str, prior_index_hash: str | None, resulting_index_hash: str,
        deployment_identifier: str | None, outcome: str, published_at: str,
    ) -> PublicationReceipt:
        return PublicationReceipt(
            edition=edition, canonical_snapshot_hash=snapshot_hash, public_export_hash=export_hash,
            edition_object_key=edition_key, index_object_key=HISTORY_INDEX_KEY,
            receipt_object_key=receipt_key, prior_index_hash=prior_index_hash,
            resulting_index_hash=resulting_index_hash, deployment_identifier=deployment_identifier,
            outcome=outcome, published_at=published_at,
        )
