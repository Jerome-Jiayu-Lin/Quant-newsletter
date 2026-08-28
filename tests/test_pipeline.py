from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from quantbrief.models import RawItem
from quantbrief.pipeline import Pipeline, canonical_url
from quantbrief.summarize import SourceSummary


class DummyClient:
    def save(self) -> None:
        pass


class PipelineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.now = datetime(2026, 8, 28, 10, tzinfo=timezone.utc)
        self.pipeline = Pipeline(client=DummyClient(), summarizer=SourceSummary(), now=self.now)  # type: ignore[arg-type]

    def item(self, *, source: str, url: str, title: str, priority: float = 1.0) -> RawItem:
        return RawItem(
            source_id=source,
            source_name=source,
            source_group="论文",
            domain="量化研究",
            title=title,
            url=url,
            summary="A useful empirical result. It includes a reproducible test.",
            published_at=self.now - timedelta(hours=2),
            retrieved_at=self.now,
            tags=["论文"],
            priority=priority,
            discovered_by=[source],
        )

    def test_canonical_url_removes_tracking(self) -> None:
        self.assertEqual(
            canonical_url("https://Example.com/paper/?utm_source=mail&a=1#top"),
            "https://example.com/paper?a=1",
        )

    def test_arxiv_versions_and_discovery_sources_merge(self) -> None:
        first = self.item(source="arXiv", url="https://arxiv.org/abs/2608.12345v1", title="A New Factor")
        second = self.item(source="HF", url="https://arxiv.org/abs/2608.12345v2", title="A New Factor", priority=0.8)
        merged = self.pipeline._deduplicate([first, second])
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0].discovered_by, ["HF", "arXiv"])

    def test_card_is_traceable(self) -> None:
        item = self.item(source="arXiv", url="https://arxiv.org/abs/2608.12345", title="A New Factor")
        card = self.pipeline._to_card(item, self.pipeline._score(item)).as_web_dict()
        self.assertEqual(card["originalUrl"], item.url)
        self.assertFalse(card["aiGenerated"])
        self.assertTrue(card["slug"])


if __name__ == "__main__":
    unittest.main()

