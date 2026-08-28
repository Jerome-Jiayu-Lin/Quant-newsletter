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
    def test_parses_rank_stars_today_and_relevant_domains(self) -> None:
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

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].title, "K-Dense-AI/scientific-agent-skills")
        self.assertEqual(items[0].domain, "AI 工具")
        self.assertEqual(items[0].metrics["trending_rank"], 1)
        self.assertEqual(items[0].metrics["trending_rank_score"], 99)
        self.assertEqual(items[0].metrics["stars"], 35710)
        self.assertEqual(items[0].metrics["stars_delta_1d"], 498)


if __name__ == "__main__":
    unittest.main()
