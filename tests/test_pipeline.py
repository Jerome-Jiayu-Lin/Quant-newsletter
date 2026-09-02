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
        self.assertEqual(card["contentType"], "article")
        self.assertFalse(card["aiGenerated"])
        self.assertTrue(card["slug"])
        self.assertEqual(card["titleEn"], item.title)
        self.assertEqual(card["tagsEn"], item.tags)
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

    def test_selection_guarantees_source_and_content_minimums_before_competing_for_slots(self) -> None:
        ranked: list[RankedItem] = []
        for index, content_type in enumerate(["paper", "paper", "article", "video"]):
            item = self.item(source=f"{content_type}-{index}", url=f"https://example.com/{index}", title=str(index))
            item.content_type = content_type
            ranked.append(RankedItem(item, 100 - index, {}))
        for index in range(3):
            item = self.item(source="github-trending-daily", url=f"https://github.com/example/{index}", title=f"repo-{index}")
            item.content_type = "repository"
            ranked.append(RankedItem(item, 50 - index, {}))

        selected = self.pipeline._select(
            ranked,
            limit=7,
            source_caps={result.item.source_id: 3 for result in ranked},
            content_caps={"paper": 2, "repository": 3, "article": 1, "video": 1},
            content_mins={"paper": 1, "repository": 1, "article": 1, "video": 1},
            source_mins={"github-trending-daily": 3},
        )

        self.assertEqual(sum(result.item.source_id == "github-trending-daily" for result in selected), 3)
        self.assertEqual({result.item.content_type for result in selected}, {"paper", "repository", "article", "video"})

    def test_global_fifteen_day_cutoff_cannot_be_extended_by_a_source(self) -> None:
        global_cutoff = self.pipeline._cutoff(lookback_hours=720, max_age_days=15)
        source_cutoff = self.pipeline._cutoff(lookback_hours=24, max_age_days=15)

        self.assertEqual(global_cutoff, self.now - timedelta(days=15))
        self.assertEqual(source_cutoff, self.now - timedelta(hours=24))

    def test_incomplete_required_sections_are_rejected(self) -> None:
        paper = self.item(source="paper", url="https://example.com/paper", title="Paper")
        paper.content_type = "paper"

        with self.assertRaisesRegex(RuntimeError, "video:1"):
            self.pipeline._validate_selection(
                [RankedItem(paper, 80, {})],
                content_mins={"paper": 1, "video": 1},
                source_mins={},
            )


if __name__ == "__main__":
    unittest.main()
