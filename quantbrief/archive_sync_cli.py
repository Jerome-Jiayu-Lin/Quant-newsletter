"""Synchronize verified R2 Public Exports into the durable local Archive."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from .archive import ArchiveReport, CardArchive
from .publication import HISTORY_INDEX_KEY, ObjectStorage
from .r2 import R2ObjectStorage


def sync_public_history(storage: ObjectStorage, archive: CardArchive) -> ArchiveReport:
    stored_index = storage.read(HISTORY_INDEX_KEY)
    if stored_index is None:
        raise ValueError("public history index not found")
    try:
        index = json.loads(stored_index.body)
        entries: list[dict[str, Any]] = index["editions"]
    except (KeyError, TypeError, json.JSONDecodeError) as error:
        raise ValueError("malformed public history index") from error

    imported = 0
    cards_imported = 0
    for entry in reversed(entries):
        edition = str(entry.get("edition", ""))
        object_key = str(entry.get("objectKey", ""))
        export_hash = str(entry.get("exportHash", ""))
        if not edition or not object_key or len(export_hash) != 64:
            raise ValueError("malformed public history entry")
        source_identifier = f"r2:{export_hash}"
        if archive.has_source(source_identifier):
            continue
        stored_edition = storage.read(object_key)
        if stored_edition is None or hashlib.sha256(stored_edition.body).hexdigest() != export_hash:
            raise ValueError(f"missing or invalid Public Export: {edition}")
        dataset = json.loads(stored_edition.body)
        if str(dataset.get("edition", "")).replace(".", "-") != edition:
            raise ValueError(f"Public Export date mismatch: {edition}")
        cards_imported += archive.ingest(dataset, source_identifier)
        imported += 1
    return ArchiveReport(len(entries), imported, cards_imported)


def main() -> None:
    parser = argparse.ArgumentParser(description="Synchronize R2 Public Exports into the local Archive")
    parser.add_argument("--database", type=Path, default=Path("storage/archive/quant-brief.sqlite3"))
    args = parser.parse_args()
    report = sync_public_history(R2ObjectStorage.from_environment(), CardArchive(args.database))
    print(
        f"editions_seen={report.editions_seen} editions_imported={report.editions_imported} "
        f"cards_imported={report.cards_imported} database={args.database}"
    )


if __name__ == "__main__":
    main()
