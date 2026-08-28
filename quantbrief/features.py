from __future__ import annotations

import re
from dataclasses import dataclass

from .models import RawItem


@dataclass(frozen=True, slots=True)
class Feature:
    id: str
    facet: str
    value: str
    label_zh: str
    label_en: str
    evidence: str
    confidence: float

    def as_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "facet": self.facet,
            "value": self.value,
            "label": {"zh": self.label_zh, "en": self.label_en},
            "evidence": self.evidence,
            "confidence": self.confidence,
        }


class FeatureExtractor:
    """Derive stable search facets from source metadata and explicit text evidence."""

    DOMAIN_FEATURES = {
        "量化研究": ("topic", "quantitative-finance", "量化金融", "Quantitative Finance"),
        "AI × 量化": ("topic", "ai-quant", "AI × 量化", "AI × Quant"),
        "开源工程": ("topic", "open-source-engineering", "开源工程", "Open-source Engineering"),
        "AI 工具": ("topic", "ai-tools", "AI 工具", "AI Tools"),
    }
    SOURCE_FEATURES = {
        "github": ("platform", "github", "GitHub", "GitHub"),
        "arxiv": ("platform", "arxiv", "arXiv", "arXiv"),
        "huggingface": ("platform", "hugging-face", "Hugging Face", "Hugging Face"),
    }
    GROUP_FEATURES = {
        "论文": ("artifact", "paper", "论文", "Paper"),
        "开源项目": ("artifact", "repository", "代码仓库", "Repository"),
        "Newsletter": ("artifact", "newsletter", "Newsletter", "Newsletter"),
        "AI 工具": ("artifact", "tool", "工具", "Tool"),
    }
    KEYWORD_FEATURES = {
        "skills": (r"\bskills?\b|技能", "topic", "skills", "Skills", "Skills"),
        "agents": (r"\bagents?\b|智能体", "topic", "agents", "智能体", "Agents"),
        "factors": (r"\bfactors?\b|因子", "topic", "factors", "因子", "Factors"),
        "portfolio": (r"\bportfolio\b|投资组合|组合优化", "topic", "portfolio", "投资组合", "Portfolio"),
        "backtesting": (r"\bbacktests?\b|回测", "method", "backtesting", "回测", "Backtesting"),
        "risk": (r"\brisk\b|风险", "topic", "risk", "风险", "Risk"),
        "forecasting": (r"\bforecast(?:ing)?\b|预测", "method", "forecasting", "预测", "Forecasting"),
        "reinforcement-learning": (
            r"\breinforcement learning\b|强化学习",
            "method",
            "reinforcement-learning",
            "强化学习",
            "Reinforcement Learning",
        ),
        "time-series": (r"\btime series\b|时间序列", "method", "time-series", "时间序列", "Time Series"),
    }

    def extract(self, item: RawItem) -> list[Feature]:
        found: dict[str, Feature] = {}
        domain = self.DOMAIN_FEATURES.get(item.domain)
        if domain:
            self._add(found, *domain, evidence="source.domain", confidence=1.0)

        source_text = f"{item.source_id} {item.source_name} {item.url}".casefold()
        for marker, spec in self.SOURCE_FEATURES.items():
            if marker in source_text:
                self._add(found, *spec, evidence="source.platform", confidence=1.0)

        group = self.GROUP_FEATURES.get(item.source_group)
        if group:
            self._add(found, *group, evidence="source.group", confidence=1.0)

        text = f"{item.title} {item.summary} {' '.join(item.tags)}"
        for pattern, facet, value, label_zh, label_en in self.KEYWORD_FEATURES.values():
            if re.search(pattern, text, re.IGNORECASE):
                self._add(found, facet, value, label_zh, label_en, evidence="content.keyword", confidence=0.8)

        return sorted(found.values(), key=lambda feature: (feature.facet, feature.value))

    @staticmethod
    def _add(
        found: dict[str, Feature],
        facet: str,
        value: str,
        label_zh: str,
        label_en: str,
        *,
        evidence: str,
        confidence: float,
    ) -> None:
        feature_id = f"{facet}:{value}"
        found[feature_id] = Feature(feature_id, facet, value, label_zh, label_en, evidence, confidence)
