from __future__ import annotations

import json
import sqlite3
import unittest
from contextlib import closing
from pathlib import Path
from tempfile import TemporaryDirectory

from quantbrief.archive import CardArchive


def dataset(edition: str, card_id: str, title: str) -> dict[str, object]:
    return {
        "edition": edition,
        "generatedAt": f"{edition}T10:00:00+08:00",
        "timezone": "Asia/Singapore",
        "cards": [
            {
                "id": card_id,
                "domain": "量化研究",
                "title": title,
                "sourceName": "arXiv",
                "originalUrl": f"https://example.com/{card_id}",
                "publishedAt": f"{edition}T00:00:00Z",
            }
        ],
    }


class CardArchiveTests(unittest.TestCase):
    def test_keeps_multiple_editions(self) -> None:
        with TemporaryDirectory() as directory:
            database = Path(directory) / "cards.sqlite3"
            archive = CardArchive(database)
            archive.ingest(dataset("2026.08.27", "a", "First"), "commit-a")
            archive.ingest(dataset("2026.08.28", "b", "Second"), "commit-b")
            with closing(sqlite3.connect(database)) as connection:
                self.assertEqual(connection.execute("SELECT COUNT(*) FROM editions").fetchone()[0], 2)
                self.assertEqual(connection.execute("SELECT COUNT(*) FROM cards").fetchone()[0], 2)

    def test_reimport_replaces_one_edition_without_duplicates(self) -> None:
        with TemporaryDirectory() as directory:
            database = Path(directory) / "cards.sqlite3"
            archive = CardArchive(database)
            archive.ingest(dataset("2026.08.28", "a", "Old"), "commit-a")
            archive.ingest(dataset("2026.08.28", "a", "Updated"), "commit-b")
            with closing(sqlite3.connect(database)) as connection:
                row = connection.execute("SELECT payload_json FROM cards").fetchone()
                self.assertEqual(json.loads(row[0])["title"], "Updated")
                self.assertEqual(connection.execute("SELECT COUNT(*) FROM editions").fetchone()[0], 1)


if __name__ == "__main__":
    unittest.main()
