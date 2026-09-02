from __future__ import annotations

import unittest

from quantbrief.publication import (
    HistoryEntry,
    PublicationReceipt,
    edition_object_key,
    history_index,
    receipt_object_key,
    sanitize_public_export,
)


def complete_card() -> dict[str, object]:
    return {
        "id": "0123456789abcdef", "slug": "example-0123456789", "domain": "量化研究",
        "contentType": "paper", "sourceName": "arXiv", "sourceGroup": "论文",
        "originalTitle": "Original", "title": "标题", "description": "描述",
        "summary": "摘要", "keyPoints": ["要点"], "whyItMatters": "价值",
        "limitations": "限制", "titleEn": "Title", "descriptionEn": "Description",
        "summaryEn": "Summary", "keyPointsEn": ["Point"], "whyItMattersEn": "Value",
        "limitationsEn": "Limits", "originalUrl": "https://example.com/paper",
        "publishedAt": "2026-09-01T00:00:00+00:00", "retrievedAt": "2026-09-01T01:00:00+00:00",
        "tags": ["研究"], "tagsEn": ["Research"], "features": [], "score": 80.0,
        "scoreBreakdown": {}, "aiGenerated": True, "summaryProvider": "test",
        "summaryModel": "test-model", "discoveredBy": ["source"],
    }


class PublicationContractTests(unittest.TestCase):
    def test_deterministic_keys_use_iso_edition_partitions(self) -> None:
        self.assertEqual(
            edition_object_key("2026-09-01"),
            "editions/v1/2026/09/2026-09-01/quant-brief-edition.json",
        )
        digest = "a" * 64
        self.assertEqual(
            receipt_object_key("2026-09-01", digest),
            f"publication-receipts/2026/09/2026-09-01/{digest}.json",
        )

    def test_sanitization_is_an_allowlist_and_normalizes_legacy_edition_date(self) -> None:
        card = complete_card()
        card["archiveOnly"] = "secret"
        export = sanitize_public_export(
            {
                "generatedAt": "2026-09-01T01:00:00+00:00", "timezone": "Asia/Singapore",
                "edition": "2026.09.01", "cards": [card], "fetchState": {"etag": "private"},
            }
        )
        self.assertEqual(export["schemaVersion"], 1)
        self.assertEqual(export["edition"], "2026-09-01")
        self.assertNotIn("fetchState", export)
        self.assertNotIn("archiveOnly", export["cards"][0])

    def test_sanitization_rejects_non_stable_card_id(self) -> None:
        card = complete_card()
        card["id"] = "temporary-id"
        with self.assertRaisesRegex(ValueError, "invalid stable id"):
            sanitize_public_export(
                {"generatedAt": "now", "timezone": "Asia/Singapore", "edition": "2026-09-01", "cards": [card]}
            )

    def test_history_index_is_unique_and_newest_first(self) -> None:
        older = HistoryEntry("2026-08-31", "old", "a" * 64, "then", 10)
        newer = HistoryEntry("2026-09-01", "new", "b" * 64, "now", 11)
        index = history_index([older, newer], "now")
        self.assertEqual(index["latestEdition"], "2026-09-01")
        self.assertEqual([entry["edition"] for entry in index["editions"]], ["2026-09-01", "2026-08-31"])
        self.assertEqual(index["editions"][0]["objectKey"], "new")
        self.assertNotIn("object_key", index["editions"][0])
        with self.assertRaisesRegex(ValueError, "duplicate Editions"):
            history_index([newer, newer], "now")

    def test_receipt_captures_required_recovery_evidence(self) -> None:
        receipt = PublicationReceipt(
            edition="2026-09-01", canonical_snapshot_hash="a" * 64,
            public_export_hash="b" * 64, edition_object_key="edition-key",
            index_object_key="editions/v1/index.json", receipt_object_key="receipt-key",
            prior_index_hash=None, resulting_index_hash="c" * 64,
            deployment_identifier=None, outcome="published", published_at="now",
        ).as_dict()
        self.assertEqual(receipt["schemaVersion"], 1)
        self.assertEqual(receipt["outcome"], "published")
        self.assertEqual(receipt["publicExportHash"], "b" * 64)
        self.assertNotIn("public_export_hash", receipt)


if __name__ == "__main__":
    unittest.main()
