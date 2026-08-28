from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone

from quantbrief.models import RawItem
from quantbrief.ranking import CohortRanker


class CohortRankerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.now = datetime(2026, 8, 28, tzinfo=timezone.utc)

    def item(self, title: str, content_type: str, metrics: dict[str, float]) -> RawItem:
        return RawItem(
            source_id=title,
            source_name=title,
            source_group="开源项目" if content_type == "repository" else "论文",
            domain="量化研究",
            title=title,
            url=f"https://example.com/{title}",
            summary="quantitative portfolio risk research",
            published_at=self.now - timedelta(days=2),
            retrieved_at=self.now,
            content_type=content_type,
            metrics=metrics,
        )

    def test_repository_stars_compete_only_with_repositories(self) -> None:
        popular_repo = self.item("popular-repo", "repository", {"stars": 1000})
        small_repo = self.item("small-repo", "repository", {"stars": 10})
        paper = self.item("paper", "paper", {"citations": 5000})
        ranked = CohortRanker().rank([small_repo, paper, popular_repo], self.now)
        by_title = {result.item.title: result for result in ranked}
        self.assertEqual(by_title["popular-repo"].breakdown["primaryMetric"], "stars")
        self.assertEqual(by_title["paper"].breakdown["primaryMetric"], "citations")
        self.assertGreater(by_title["popular-repo"].score, by_title["small-repo"].score)

    def test_missing_metric_uses_fallback_instead_of_zero(self) -> None:
        measured = self.item("measured", "paper", {"citations": 2})
        missing = self.item("missing", "paper", {})
        ranked = CohortRanker().rank([measured, missing], self.now)
        by_title = {result.item.title: result for result in ranked}
        self.assertEqual(by_title["missing"].breakdown["mode"], "relevance-fallback")
        self.assertIsNone(by_title["missing"].breakdown["primaryMetricValue"])

    def test_video_uses_views(self) -> None:
        video = self.item("video", "video", {"views": 100})
        result = CohortRanker().rank([video], self.now)[0]
        self.assertEqual(result.breakdown["primaryMetric"], "views")

    def test_repository_velocity_can_use_repository_age(self) -> None:
        old_repo = self.item("old", "repository", {"stars": 100, "metric_age_days": 1000})
        young_repo = self.item("young", "repository", {"stars": 100, "metric_age_days": 10})
        ranked = CohortRanker().rank([old_repo, young_repo], self.now)
        by_title = {result.item.title: result for result in ranked}
        self.assertGreater(
            by_title["young"].breakdown["velocityPercentile"],
            by_title["old"].breakdown["velocityPercentile"],
        )


if __name__ == "__main__":
    unittest.main()
