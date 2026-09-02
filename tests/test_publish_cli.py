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
    def test_shared_entry_publishes_then_updates_compatibility_export(self) -> None:
        with TemporaryDirectory() as directory:
            snapshot = Path(directory) / "quant-brief-edition.json"
            compatibility = Path(directory) / "latest-public-edition.json"
            snapshot.write_text(json.dumps(complete_snapshot()), encoding="utf-8")
            receipt = publish_snapshot(
                snapshot, FakeStorage(), compatibility_export=compatibility,
                deployment_identifier="test:123", published_at="2026-09-02T00:00:00Z",
            )
            exported = json.loads(compatibility.read_text(encoding="utf-8"))
            self.assertEqual(exported["schemaVersion"], 1)
            self.assertEqual(exported["edition"], "2026-09-01")
            self.assertEqual(receipt.deployment_identifier, "test:123")

    def test_remote_failure_does_not_replace_compatibility_export(self) -> None:
        with TemporaryDirectory() as directory:
            snapshot = Path(directory) / "quant-brief-edition.json"
            compatibility = Path(directory) / "latest-public-edition.json"
            snapshot.write_text(json.dumps(complete_snapshot()), encoding="utf-8")
            compatibility.write_text("preserve me", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "remote unavailable"):
                publish_snapshot(snapshot, FailingStorage(), compatibility_export=compatibility)
            self.assertEqual(compatibility.read_text(encoding="utf-8"), "preserve me")


if __name__ == "__main__":
    unittest.main()
