from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from quantbrief.candidates import CandidatePool
from quantbrief.models import RawItem


class CandidatePoolTests(unittest.TestCase):
    def setUp(self) -> None:
        self.now = datetime(2026, 8, 31, tzinfo=timezone.utc)

    def item(self, title: str, age_hours: int, *, source_id: str = "article", metrics=None) -> RawItem:
        return RawItem(
            source_id=source_id,
            source_name=source_id,
            source_group="网站与论坛",
            domain="量化研究",
            title=title,
            url=f"https://example.com/{title}",
            summary="A useful empirical analysis.",
            published_at=self.now - timedelta(hours=age_hours),
            retrieved_at=self.now,
            metrics=metrics or {},
        )

    def test_splits_forty_eight_hour_primary_lane_from_fifteen_day_carryover(self) -> None:
        pool = CandidatePool()
        pool.ingest(
            [("fresh", self.item("fresh", 47)), ("carry", self.item("carry", 49)), ("old", self.item("old", 361))],
            self.now,
            15,
        )

        primary, carryover = pool.selection_lanes(
            self.now, primary_window_hours=48, max_age_days=15, current_edition="2026.08.31"
        )

        self.assertEqual([item.title for item in primary], ["fresh"])
        self.assertEqual([item.title for item in carryover], ["carry"])

    def test_published_candidate_is_not_selected_again(self) -> None:
        pool = CandidatePool()
        item = self.item("published", 1)
        pool.ingest([("same", item)], self.now, 15)
        pool.mark_published([("same", item)], self.now - timedelta(days=1), "2026.08.30")

        primary, carryover = pool.selection_lanes(
            self.now, primary_window_hours=48, max_age_days=15, current_edition="2026.08.31"
        )

        self.assertEqual(primary + carryover, [])

    def test_same_edition_rerun_remains_idempotently_eligible(self) -> None:
        pool = CandidatePool()
        item = self.item("same-edition", 1)
        pool.ingest([("same", item)], self.now, 15)
        pool.mark_published([("same", item)], self.now, "2026.08.31")

        primary, _ = pool.selection_lanes(
            self.now, primary_window_hours=48, max_age_days=15, current_edition="2026.08.31"
        )

        self.assertEqual([candidate.title for candidate in primary], ["same-edition"])

    def test_trending_repository_can_return_only_on_anomalous_growth(self) -> None:
        pool = CandidatePool()
        initial = self.item(
            "repo", 0, source_id="github-trending-daily", metrics={"stars": 1000, "stars_delta_1d": 100}
        )
        pool.mark_published([("repo", initial)], self.now - timedelta(days=1), "2026.08.30")
        ordinary = self.item(
            "repo", 0, source_id="github-trending-daily", metrics={"stars": 1200, "stars_delta_1d": 150}
        )
        pool.ingest([("repo", ordinary)], self.now, 15)
        self.assertEqual(
            pool.selection_lanes(
                self.now, primary_window_hours=48, max_age_days=15, current_edition="2026.08.31"
            )[0],
            [],
        )

        anomalous = self.item(
            "repo", 0, source_id="github-trending-daily", metrics={"stars": 2300, "stars_delta_1d": 600}
        )
        pool.ingest([("repo", anomalous)], self.now, 15)
        self.assertEqual(
            pool.selection_lanes(
                self.now, primary_window_hours=48, max_age_days=15, current_edition="2026.08.31"
            )[0][0].title,
            "repo",
        )

    def test_pool_round_trips_as_independent_runtime_content(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "rolling-candidate-pool.json"
            pool = CandidatePool(path)
            item = self.item("saved", 3)
            pool.ingest([("saved", item)], self.now, 15)
            pool.save(self.now)

            loaded = CandidatePool(path)
            primary, _ = loaded.selection_lanes(
                self.now, primary_window_hours=48, max_age_days=15, current_edition="2026.08.31"
            )

            self.assertEqual(primary[0].title, "saved")


if __name__ == "__main__":
    unittest.main()
