from __future__ import annotations

import unittest
from datetime import datetime, timezone

from quantbrief.features import FeatureExtractor
from quantbrief.models import RawItem


class FeatureExtractorTests(unittest.TestCase):
    def test_combines_source_domain_and_keyword_evidence(self) -> None:
        now = datetime(2026, 8, 28, tzinfo=timezone.utc)
        item = RawItem(
            source_id="github-trending",
            source_name="GitHub",
            source_group="开源项目",
            domain="量化研究",
            title="Quantitative Skills for Portfolio Risk",
            url="https://github.com/example/research-skills",
            summary="A portfolio risk research repository.",
            published_at=now,
            retrieved_at=now,
        )

        features = {feature.id: feature for feature in FeatureExtractor().extract(item)}

        self.assertIn("platform:github", features)
        self.assertIn("artifact:repository", features)
        self.assertIn("topic:quantitative-finance", features)
        self.assertIn("topic:skills", features)
        self.assertEqual(features["platform:github"].evidence, "source.platform")
        self.assertEqual(features["topic:skills"].evidence, "content.keyword")

    def test_does_not_invent_a_trending_rank(self) -> None:
        now = datetime(2026, 8, 28, tzinfo=timezone.utc)
        item = RawItem(
            source_id="github",
            source_name="GitHub",
            source_group="开源项目",
            domain="开源工程",
            title="A trending repository",
            url="https://github.com/example/repo",
            summary="Popular today.",
            published_at=now,
            retrieved_at=now,
        )
        feature_ids = {feature.id for feature in FeatureExtractor().extract(item)}
        self.assertFalse(any(feature.startswith("ranking:") for feature in feature_ids))


if __name__ == "__main__":
    unittest.main()
