from __future__ import annotations

import unittest
from datetime import datetime, timezone

from quantbrief.http import HttpResponse
from quantbrief.sources import GitHubTrendingAdapter


class FakeClient:
    def __init__(self, body: str) -> None:
        self.body = body

    def get(self, url: str, **kwargs) -> HttpResponse:
        return HttpResponse(200, self.body.encode("utf-8"), {})


class GitHubTrendingAdapterTests(unittest.TestCase):
    def test_collects_the_ordered_trending_list_for_history_aware_selection(self) -> None:
        html = """
        <article class="Box-row">
          <h2><a href="/K-Dense-AI/scientific-agent-skills">K-Dense-AI / scientific-agent-skills</a></h2>
          <p class="col-9 color-fg-muted my-1 pr-4">Turn an AI agent into an AI Scientist with validated skills.</p>
          <span itemprop="programmingLanguage">Python</span>
          <a href="/K-Dense-AI/scientific-agent-skills/stargazers">35,710</a>
          <span class="float-sm-right">498 stars today</span>
        </article>
        <article class="Box-row">
          <h2><a href="/games/irrelevant">games / irrelevant</a></h2>
          <p class="col-9">A retro game engine.</p>
          <a href="/games/irrelevant/stargazers">100</a>
          <span>50 stars today</span>
        </article>
        <article class="Box-row">
          <h2><a href="/tools/third">tools / third</a></h2>
          <p class="col-9">A small developer utility.</p>
          <span>40 stars today</span>
        </article>
        <article class="Box-row">
          <h2><a href="/tools/fourth">tools / fourth</a></h2>
          <p class="col-9">Must not enter the daily top three.</p>
          <span>30 stars today</span>
        </article>
        """
        source = {
            "id": "github-trending-daily",
            "name": "GitHub Trending Daily",
            "group": "开源项目",
            "domain": "开源工程",
            "url": "https://github.com/trending?since=daily",
            "tags": ["GitHub Trending"],
        }
        now = datetime(2026, 8, 28, tzinfo=timezone.utc)

        items = GitHubTrendingAdapter().fetch(source, FakeClient(html), now)  # type: ignore[arg-type]

        self.assertEqual(len(items), 4)
        self.assertEqual(items[0].title, "K-Dense-AI/scientific-agent-skills")
        self.assertEqual(items[0].domain, "AI 工具")
        self.assertEqual(items[0].metrics["trending_rank"], 1)
        self.assertEqual(items[0].metrics["trending_rank_score"], 99)
        self.assertEqual(items[0].metrics["stars"], 35710)
        self.assertEqual(items[0].metrics["stars_delta_1d"], 498)
        self.assertEqual(items[1].title, "games/irrelevant")
        self.assertEqual(items[2].metrics["trending_rank"], 3)
        self.assertEqual(items[3].title, "tools/fourth")

    def test_youtube_feed_exposes_description_and_views(self) -> None:
        xml = """
        <feed xmlns="http://www.w3.org/2005/Atom" xmlns:media="http://search.yahoo.com/mrss/">
          <entry>
            <title>Walk-forward validation for factor strategies</title>
            <link rel="alternate" href="https://www.youtube.com/watch?v=abc" />
            <published>2026-08-27T00:00:00+00:00</published>
            <media:group>
              <media:description>Tests a factor model out of sample with costs.</media:description>
              <media:community><media:statistics views="1234" /></media:community>
            </media:group>
          </entry>
        </feed>
        """
        source = {
            "id": "quant-video",
            "name": "Quant Video",
            "group": "视频",
            "domain": "量化研究",
            "url": "https://www.youtube.com/feeds/videos.xml?channel_id=example",
        }
        now = datetime(2026, 8, 28, tzinfo=timezone.utc)

        from quantbrief.sources import RssAdapter
        items = RssAdapter().fetch(source, FakeClient(xml), now)  # type: ignore[arg-type]

        self.assertEqual(items[0].content_type, "video")
        self.assertIn("out of sample", items[0].summary)
        self.assertEqual(items[0].metrics["views"], 1234)


if __name__ == "__main__":
    unittest.main()
