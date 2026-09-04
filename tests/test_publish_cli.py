from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from quantbrief.publish_cli import publish_snapshot
from tests.test_publication import FakeStorage, complete_snapshot


class FailingStorage(FakeStorage):
    def write(self, key: str, body: bytes, expected_version: str | None):
        raise RuntimeError("remote unavailable")


class PublishCliTests(unittest.TestCase):
    def test_shared_entry_publishes_snapshot_and_returns_receipt(self) -> None:
        with TemporaryDirectory() as directory:
            snapshot = Path(directory) / "quant-brief-edition.json"
            snapshot.write_text(json.dumps(complete_snapshot()), encoding="utf-8")
            receipt = publish_snapshot(
                snapshot, FakeStorage(),
                deployment_identifier="test:123", published_at="2026-09-02T00:00:00Z",
            )
            self.assertEqual(receipt.edition, "2026-09-01")
            self.assertEqual(receipt.deployment_identifier, "test:123")

    def test_remote_failure_is_reported(self) -> None:
        with TemporaryDirectory() as directory:
            snapshot = Path(directory) / "quant-brief-edition.json"
            snapshot.write_text(json.dumps(complete_snapshot()), encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "remote unavailable"):
                publish_snapshot(snapshot, FailingStorage())


if __name__ == "__main__":
    unittest.main()
