from __future__ import annotations

import math
import re
from dataclasses import dataclass
from datetime import datetime

from .models import RawItem


PRIMARY_METRICS = {
    "paper": ("citations", "upvotes"),
    "video": ("views",),
    "repository": ("trending_rank_score", "stars_delta_1d", "stars"),
    "article": ("engagement",),
}

EVIDENCE_PATTERNS = {
    "out_of_sample": r"out[- ]of[- ]sample|walk[- ]forward|holdout|样本外|滚动验证",
    "empirical_test": r"backtest|experiment|benchmark|ablation|robustness|回测|实验|基准|消融|稳健",
    "data_scope": r"dataset|observations?|sample|panel|\bdata\b|数据集|观测|样本",
    "evaluation": r"auc|sharpe|sortino|drawdown|accuracy|f1|r\s*[²2]|mape|crps|p[- ]?value|t[- ]?stat",
    "realism": r"transaction costs?|slippage|market impact|fees?|operational costs?|交易成本|滑点|冲击成本",
}
ACTION_PATTERNS = {
    "implementation": r"implementation|tutorial|how to|framework|library|api|workflow|部署|实现|教程|框架|工作流",
    "reproducibility": r"reproducible|open[- ]source|source code|github|replicat|可复现|开源|源码|复现",
    "decision_use": r"strategy|portfolio|risk management|execution|trading|allocation|策略|组合|风险管理|执行|交易",
}
NOVELTY_PATTERN = r"introduc|propos|new method|finds? that|outperform|release|首次|提出|发现|优于|发布"
ROUNDUP_PATTERN = r"recent .* links|daily (?:roundup|wrap)|weekly links|link roundup|每日汇总|链接汇总"


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
                content_value, content_signals = self._content_value(item, relevance)
                source_quality = max(0.0, min(100.0, item.priority * 100.0))
                if metric_percentile is None:
                    score = content_value * 0.70 + freshness * 0.20 + source_quality * 0.10
                    objective = None
                    mode = "relevance-fallback"
                else:
                    objective = metric_percentile * 0.6 + (velocity_percentile or 0.0) * 0.4
                    score = objective * 0.35 + content_value * 0.40 + freshness * 0.15 + source_quality * 0.10
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
                            "contentValueScore": round(content_value, 2),
                            "contentSignals": content_signals,
                            "freshnessScore": round(freshness, 2),
                            "sourceQualityScore": round(source_quality, 2),
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
        return max(0.0, 100.0 * (1.0 - age_days / 15.0))

    @staticmethod
    def _content_value(item: RawItem, relevance: float) -> tuple[float, dict[str, float]]:
        text = f"{item.title} {item.summary}".casefold()
        evidence_hits = sum(bool(re.search(pattern, text, re.I)) for pattern in EVIDENCE_PATTERNS.values())
        action_hits = sum(bool(re.search(pattern, text, re.I)) for pattern in ACTION_PATTERNS.values())
        novelty = 8.0 if re.search(NOVELTY_PATTERN, text, re.I) else 0.0
        number_hits = len(re.findall(r"(?<!\w)\d+(?:[.,]\d+)?%?", text))
        specificity = min(10.0, number_hits * 2.0 + len(item.summary) / 400.0)
        penalty = -25.0 if re.search(ROUNDUP_PATTERN, text, re.I) else 0.0
        signals = {
            "evidence": min(25.0, evidence_hits * 5.0),
            "actionability": min(15.0, action_hits * 5.0),
            "novelty": novelty,
            "specificity": round(specificity, 2),
            "penalty": penalty,
        }
        score = relevance * 0.45 + sum(signals.values())
        return max(0.0, min(100.0, score)), signals

    @staticmethod
    def _rounded(value: float | None) -> float | None:
        return None if value is None else round(value, 2)
