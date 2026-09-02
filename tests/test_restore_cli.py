from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from quantbrief.publication import Publisher
from quantbrief.restore_cli import restore_publication
from tests.test_publication import FakeStorage, complete_snapshot


class RestoreCliTests(unittest.TestCase):
    def test_restore_command_retains_machine_readable_receipt(self) -> None:
        storage = FakeStorage()
        publisher = Publisher(storage)
        first = publisher.publish(complete_snapshot(), published_at="2026-09-02T00:00:00Z")
        changed = complete_snapshot()
        changed["cards"][0]["title"] = "changed"  # type: ignore[index]
        publisher.publish(changed, published_at="2026-09-02T01:00:00Z")
        with TemporaryDirectory() as directory:
            path = Path(directory) / "restore-receipt.json"
            receipt = restore_publication(
                first.resulting_index_hash, storage, deployment_identifier="fake-drill",
                restored_at="2026-09-02T02:00:00Z", receipt_path=path,
            )
            retained = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(receipt.outcome, "restored")
        self.assertEqual(retained["restoredIndexHash"], first.resulting_index_hash)
        self.assertEqual(retained["deploymentIdentifier"], "fake-drill")


if __name__ == "__main__":
    unittest.main()
