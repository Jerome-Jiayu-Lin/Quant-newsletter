from __future__ import annotations

import argparse
import json
import sqlite3
import subprocess
from contextlib import closing
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class ArchiveReport:
    editions_seen: int
    editions_imported: int
    cards_imported: int


class CardArchive:
    """Local source of truth for durable editions behind one ingestion interface."""

    def __init__(self, database: Path) -> None:
        self.database = database

    def ingest_file(self, path: Path, source_commit: str | None = None) -> int:
        return self.ingest(json.loads(path.read_text(encoding="utf-8")), source_commit)

    def ingest(self, dataset: dict[str, Any], source_commit: str | None = None) -> int:
        edition = str(dataset["edition"])
        cards = dataset.get("cards", [])
        self.database.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(self.database)) as connection:
            self._create_schema(connection)
            connection.execute("BEGIN")
            connection.execute(
                """
                INSERT INTO editions (edition, generated_at, timezone, source_commit, imported_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(edition) DO UPDATE SET
                    generated_at=excluded.generated_at,
                    timezone=excluded.timezone,
                    source_commit=COALESCE(excluded.source_commit, editions.source_commit),
                    imported_at=excluded.imported_at
                """,
                (
                    edition,
                    dataset.get("generatedAt"),
                    dataset.get("timezone", "Asia/Singapore"),
                    source_commit,
                    datetime.now(timezone.utc).isoformat(),
                ),
            )
            connection.execute("DELETE FROM cards WHERE edition = ?", (edition,))
            connection.executemany(
                """
                INSERT INTO cards
                    (edition, card_id, domain, title, source_name, original_url, published_at,
                     summary_provider, summary_model, payload_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        edition,
                        card["id"],
                        card.get("domain"),
                        card.get("title"),
                        card.get("sourceName"),
                        card.get("originalUrl"),
                        card.get("publishedAt"),
                        card.get("summaryProvider", "source"),
                        card.get("summaryModel"),
                        json.dumps(card, ensure_ascii=False, separators=(",", ":")),
                    )
                    for card in cards
                ],
            )
            connection.executemany(
                """
                INSERT INTO card_features
                    (edition, card_id, feature_id, facet, value, label_zh, label_en, evidence, confidence)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        edition,
                        card["id"],
                        feature["id"],
                        feature["facet"],
                        feature["value"],
                        feature["label"]["zh"],
                        feature["label"]["en"],
                        feature["evidence"],
                        feature["confidence"],
                    )
                    for card in cards
                    for feature in card.get("features", [])
                ],
            )
            if source_commit:
                connection.execute(
                    "INSERT OR IGNORE INTO imports (source_commit, edition, imported_at) VALUES (?, ?, ?)",
                    (source_commit, edition, datetime.now(timezone.utc).isoformat()),
                )
            connection.commit()
        return len(cards)

    def search(self, *, edition: str | None = None, feature_ids: list[str] | None = None) -> list[dict[str, Any]]:
        """Return cards matching an optional date and every requested Feature."""
        if not self.database.exists():
            return []
        requested = sorted(set(feature_ids or []))
        conditions: list[str] = []
        parameters: list[Any] = []
        if edition:
            conditions.append("cards.edition = ?")
            parameters.append(edition)
        if requested:
            placeholders = ",".join("?" for _ in requested)
            conditions.append(
                "cards.card_id IN ("
                "SELECT card_id FROM card_features "
                "WHERE edition = cards.edition AND feature_id IN (" + placeholders + ") "
                "GROUP BY card_id HAVING COUNT(DISTINCT feature_id) = ?"
                ")"
            )
            parameters.extend(requested)
            parameters.append(len(requested))
        where = " WHERE " + " AND ".join(conditions) if conditions else ""
        query = "SELECT payload_json FROM cards" + where + " ORDER BY published_at DESC"
        with closing(sqlite3.connect(self.database)) as connection:
            self._create_schema(connection)
            return [json.loads(row[0]) for row in connection.execute(query, parameters)]

    def sync_git_history(self, repo: Path, data_path: str = "web/data/cards.json") -> ArchiveReport:
        commits = self._git(repo, "log", "--reverse", "--format=%H", "--", data_path).splitlines()
        imported = 0
        cards_imported = 0
        known = self._known_commits()
        for commit in commits:
            commit = commit.strip()
            if not commit or commit in known:
                continue
            raw = self._git(repo, "show", f"{commit}:{data_path}")
            cards_imported += self.ingest(json.loads(raw), commit)
            imported += 1
        return ArchiveReport(len(commits), imported, cards_imported)

    def has_source(self, source_identifier: str) -> bool:
        return source_identifier in self._known_commits()

    def _known_commits(self) -> set[str]:
        if not self.database.exists():
            return set()
        with closing(sqlite3.connect(self.database)) as connection:
            self._create_schema(connection)
            return {row[0] for row in connection.execute("SELECT source_commit FROM imports")}

    @staticmethod
    def _git(repo: Path, *arguments: str) -> str:
        completed = subprocess.run(
            ["git", *arguments], cwd=repo, check=True, capture_output=True, text=True, encoding="utf-8"
        )
        return completed.stdout

    @staticmethod
    def _create_schema(connection: sqlite3.Connection) -> None:
        connection.executescript(
            """
            PRAGMA journal_mode=WAL;
            PRAGMA foreign_keys=ON;
            CREATE TABLE IF NOT EXISTS editions (
                edition TEXT PRIMARY KEY,
                generated_at TEXT,
                timezone TEXT NOT NULL,
                source_commit TEXT UNIQUE,
                imported_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS cards (
                edition TEXT NOT NULL REFERENCES editions(edition) ON DELETE CASCADE,
                card_id TEXT NOT NULL,
                domain TEXT,
                title TEXT,
                source_name TEXT,
                original_url TEXT,
                published_at TEXT,
                summary_provider TEXT NOT NULL DEFAULT 'source',
                summary_model TEXT,
                payload_json TEXT NOT NULL,
                PRIMARY KEY (edition, card_id)
            );
            CREATE TABLE IF NOT EXISTS imports (
                source_commit TEXT PRIMARY KEY,
                edition TEXT NOT NULL,
                imported_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS card_features (
                edition TEXT NOT NULL,
                card_id TEXT NOT NULL,
                feature_id TEXT NOT NULL,
                facet TEXT NOT NULL,
                value TEXT NOT NULL,
                label_zh TEXT NOT NULL,
                label_en TEXT NOT NULL,
                evidence TEXT NOT NULL,
                confidence REAL NOT NULL,
                PRIMARY KEY (edition, card_id, feature_id),
                FOREIGN KEY (edition, card_id) REFERENCES cards(edition, card_id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS cards_domain_idx ON cards(domain);
            CREATE INDEX IF NOT EXISTS cards_published_idx ON cards(published_at);
            CREATE INDEX IF NOT EXISTS card_features_lookup_idx ON card_features(feature_id, edition);
            """
        )
        CardArchive._ensure_column(connection, "cards", "summary_provider", "TEXT NOT NULL DEFAULT 'source'")
        CardArchive._ensure_column(connection, "cards", "summary_model", "TEXT")

    @staticmethod
    def _ensure_column(connection: sqlite3.Connection, table: str, column: str, declaration: str) -> None:
        existing = {row[1] for row in connection.execute(f"PRAGMA table_info({table})")}
        if column not in existing:
            connection.execute(f"ALTER TABLE {table} ADD COLUMN {column} {declaration}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Synchronize Git history into the local Quant Brief archive")
    parser.add_argument("--database", type=Path, default=Path("storage/archive/quant-brief.sqlite3"))
    parser.add_argument("--repo", type=Path, default=Path("."))
    parser.add_argument("--data-path", default="web/data/cards.json")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    report = CardArchive(args.database).sync_git_history(args.repo.resolve(), args.data_path)
    print(
        f"editions_seen={report.editions_seen} editions_imported={report.editions_imported} "
        f"cards_imported={report.cards_imported} database={args.database}"
    )


if __name__ == "__main__":
    main()
