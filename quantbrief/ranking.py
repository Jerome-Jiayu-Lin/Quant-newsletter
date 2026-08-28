from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime

from .models import RawItem


PRIMARY_METRICS = {
    "paper": ("citations", "upvotes"),
    "video": ("views",),
    "repository": ("trending_rank_score", "stars_delta_1d", "stars"),
    "article": ("engagement",),
}


@dataclass(frozen=True, slots=True)
class RankedItem:
    item: RawItem
    score: float
    breakdown: dict[str, object]


class CohortRanker:
    """Compare objective popularity only within the same content-type cohort."""

    def rank(self, items: list[RawItem], now: datetime) -> list[RankedItem]:
        cohorts: dict[str, list[RawItem]] = {}
        for item in items:
            cohorts.setdefault(item.content_type, []).append(item)
        results: list[RankedItem] = []
        for content_type, cohort in cohorts.items():
            metric_name = self._metric_for_cohort(content_type, cohort)
            raw_values = {id(item): self._metric_value(item, metric_name) for item in cohort}
            observed = [value for value in raw_values.values() if value is not None]
            velocity_values = {
                id(item): (
                    math.log1p(raw_values[id(item)]) / self._metric_age_days(item, now)
                    if raw_values[id(item)] is not None
                    else None
                )
                for item in cohort
            }
            observed_velocity = [value for value in velocity_values.values() if value is not None]
            for item in cohort:
                metric_value = raw_values[id(item)]
                metric_percentile = self._percentile(metric_value, observed)
                velocity_percentile = self._percentile(velocity_values[id(item)], observed_velocity)
                relevance = self._relevance(item)
                freshness = self._freshness(item, now)
                if metric_percentile is None:
                    score = relevance * 0.65 + freshness * 0.35
                    objective = None
                    mode = "relevance-fallback"
                else:
                    objective = metric_percentile * 0.6 + (velocity_percentile or 0.0) * 0.4
                    score = objective * 0.70 + relevance * 0.20 + freshness * 0.10
                    mode = "cohort-metric"
                results.append(
                    RankedItem(
                        item=item,
                        score=round(score, 2),
                        breakdown={
                            "contentType": content_type,
                            "comparisonCohortSize": len(cohort),
                            "mode": mode,
                            "primaryMetric": metric_name,
                            "primaryMetricValue": metric_value,
                            "metricPercentile": self._rounded(metric_percentile),
                            "velocityPercentile": self._rounded(velocity_percentile),
                            "objectiveScore": self._rounded(objective),
                            "relevanceScore": round(relevance, 2),
                            "freshnessScore": round(freshness, 2),
                            "sourceMetrics": dict(item.metrics),
                        },
                    )
                )
        return sorted(results, key=lambda result: result.score, reverse=True)

    @staticmethod
    def _metric_for_cohort(content_type: str, cohort: list[RawItem]) -> str | None:
        for metric in PRIMARY_METRICS.get(content_type, ()):
            if any(metric in item.metrics for item in cohort):
                return metric
        return None

    @staticmethod
    def _metric_value(item: RawItem, metric: str | None) -> float | None:
        if not metric or metric not in item.metrics:
            return None
        return max(0.0, float(item.metrics[metric]))

    @staticmethod
    def _metric_age_days(item: RawItem, now: datetime) -> float:
        explicit = item.metrics.get("metric_age_days")
        if explicit is not None:
            return max(1.0, float(explicit))
        return max(1.0, (now - item.published_at).total_seconds() / 86400)

    @staticmethod
    def _percentile(value: float | None, observed: list[float]) -> float | None:
        if value is None or not observed:
            return None
        if len(observed) == 1:
            return 100.0
        below = sum(candidate < value for candidate in observed)
        equal = sum(candidate == value for candidate in observed)
        return 100.0 * (below + 0.5 * (equal - 1)) / (len(observed) - 1)

    @staticmethod
    def _relevance(item: RawItem) -> float:
        text = f"{item.title} {item.summary}".casefold()
        terms = {
            "backtest", "trading", "portfolio", "factor", "alpha", "market making", "order book",
            "execution", "volatility", "risk", "asset pricing", "forecast", "causal", "agent",
            "time series", "reinforcement learning", "回测", "交易", "组合", "因子", "风险", "预测",
        }
        matches = sum(term in text for term in terms)
        domain_base = {"量化研究": 75, "AI × 量化": 70, "开源工程": 55, "AI 工具": 55}.get(item.domain, 35)
        return min(100.0, domain_base + matches * 5)

    @staticmethod
    def _freshness(item: RawItem, now: datetime) -> float:
        age_days = max(0.0, (now - item.published_at).total_seconds() / 86400)
        return max(0.0, 100.0 - age_days * 12.5)

    @staticmethod
    def _rounded(value: float | None) -> float | None:
        return None if value is None else round(value, 2)
