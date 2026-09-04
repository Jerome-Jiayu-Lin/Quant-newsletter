from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from quantbrief.archive import CardArchive
from quantbrief.archive_sync_cli import sync_public_history
from quantbrief.publication import HISTORY_INDEX_KEY, StoredObject

from tests.test_archive import dataset


class FakeStorage:
    def __init__(self, objects: dict[str, bytes]) -> None:
        self.objects = objects

    def read(self, key: str) -> StoredObject | None:
        body = self.objects.get(key)
        return StoredObject(body, key) if body is not None else None

    def write(self, key: str, body: bytes, expected_version: str | None) -> StoredObject:
        raise AssertionError("synchronization must be read-only")


class ArchiveSyncTests(unittest.TestCase):
    def test_imports_verified_exports_idempotently(self) -> None:
        export = json.dumps(dataset("2026.09.01", "card-a", "Verified"), separators=(",", ":")).encode()
        export_hash = hashlib.sha256(export).hexdigest()
        object_key = "editions/v1/2026/09/2026-09-01/quant-brief-edition.json"
        index = json.dumps({
            "schemaVersion": 1,
            "editions": [{"edition": "2026-09-01", "objectKey": object_key, "exportHash": export_hash}],
        }).encode()
        storage = FakeStorage({HISTORY_INDEX_KEY: index, object_key: export})
        with TemporaryDirectory() as directory:
            archive = CardArchive(Path(directory) / "archive.sqlite3")
            first = sync_public_history(storage, archive)
            second = sync_public_history(storage, archive)
        self.assertEqual((first.editions_imported, first.cards_imported), (1, 1))
        self.assertEqual((second.editions_imported, second.cards_imported), (0, 0))

    def test_rejects_an_export_with_the_wrong_hash(self) -> None:
        object_key = "editions/v1/2026/09/2026-09-01/quant-brief-edition.json"
        index = json.dumps({
            "schemaVersion": 1,
            "editions": [{"edition": "2026-09-01", "objectKey": object_key, "exportHash": "0" * 64}],
        }).encode()
        with TemporaryDirectory() as directory:
            archive = CardArchive(Path(directory) / "archive.sqlite3")
            with self.assertRaisesRegex(ValueError, "missing or invalid Public Export"):
                sync_public_history(FakeStorage({HISTORY_INDEX_KEY: index, object_key: b"{}"}), archive)


if __name__ == "__main__":
    unittest.main()
