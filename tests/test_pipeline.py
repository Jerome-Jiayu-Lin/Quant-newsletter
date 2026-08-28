from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from quantbrief.models import RawItem
from quantbrief.pipeline import Pipeline, canonical_url
from quantbrief.ranking import CohortRanker, RankedItem
from quantbrief.summarize import SourceSummary


class DummyClient:
    def save(self) -> None:
        pass


class FailingSummarizer:
    def summarize(self, item: RawItem):
        raise RuntimeError("provider unavailable")


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
        ranked = CohortRanker().rank([item], self.now)[0]
        card = self.pipeline._to_card(item, ranked.score, ranked.breakdown).as_web_dict()
        self.assertEqual(card["originalUrl"], item.url)
        self.assertFalse(card["aiGenerated"])
        self.assertTrue(card["slug"])
        self.assertEqual(card["titleEn"], item.title)
        self.assertIn("topic:quantitative-finance", {feature["id"] for feature in card["features"]})

    def test_strict_summary_mode_does_not_silently_fallback(self) -> None:
        pipeline = Pipeline(
            client=DummyClient(),
            summarizer=FailingSummarizer(),
            now=self.now,
            strict_summaries=True,
        )  # type: ignore[arg-type]
        item = self.item(source="arXiv", url="https://arxiv.org/abs/2608.12345", title="A New Factor")
        with self.assertRaisesRegex(RuntimeError, "AI summary failed"):
            pipeline._to_card(item, 50.0)

    def test_selection_respects_content_caps_before_filling_spare_slots(self) -> None:
        papers = [
            RankedItem(self.item(source=f"paper-{index}", url=f"https://example.com/p{index}", title=f"Paper {index}"), 90 - index, {})
            for index in range(3)
        ]
        repository = self.item(source="repo", url="https://example.com/repo", title="Repository")
        repository.content_type = "repository"
        ranked = papers + [RankedItem(repository, 50, {})]
        selected = self.pipeline._select(
            ranked,
            limit=3,
            source_caps={item.item.source_id: 3 for item in ranked},
            content_caps={"article": 2, "repository": 1},
        )
        self.assertEqual([result.item.content_type for result in selected], ["article", "article", "repository"])


if __name__ == "__main__":
    unittest.main()
