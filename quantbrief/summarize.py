from __future__ import annotations

import json
import os
import re
import urllib.request
from dataclasses import dataclass
from typing import Any, Protocol

from .models import RawItem


@dataclass(slots=True)
class SummaryResult:
    title: str
    description: str
    summary: str
    key_points: list[str]
    why_it_matters: str
    limitations: str
    tags: list[str]
    ai_generated: bool


class Summarizer(Protocol):
    def summarize(self, item: RawItem) -> SummaryResult: ...


def _sentences(text: str) -> list[str]:
    cleaned = re.sub(r"\s+", " ", text).strip()
    return [part.strip() for part in re.split(r"(?<=[。！？.!?])\s+", cleaned) if part.strip()]


class SourceSummary:
    """Reliable fallback when no model credential is configured."""

    def summarize(self, item: RawItem) -> SummaryResult:
        sentences = _sentences(item.summary)
        description = (sentences[0] if sentences else item.title)[:180]
        summary = item.summary[:1200] or f"来源发布了新内容：{item.title}。请打开原文核对完整论证与数据。"
        domain_reason = {
            "量化研究": "可用于评估新的研究假设、实证证据或策略风险。",
            "AI × 量化": "可能改善量化研究中的数据处理、实验设计或自动化工作流。",
            "开源工程": "可能影响现有研究工具链的能力、可靠性或复现方式。",
            "AI 工具": "可用于判断工具更新是否值得纳入日常研究流程。",
        }.get(item.domain, "可作为进一步研究与工具筛选的线索。")
        return SummaryResult(
            title=item.title,
            description=description,
            summary=summary,
            key_points=(sentences[:3] or [description]),
            why_it_matters=domain_reason,
            limitations="当前为来源摘要整理，尚未独立核验全文、数据与实验结果。",
            tags=item.tags[:6],
            ai_generated=False,
        )


class OpenAIResponsesSummary:
    """Chinese knowledge cards through the Responses API structured-output seam."""

    endpoint = "https://api.openai.com/v1/responses"

    def __init__(self, api_key: str, model: str = "gpt-5.6-luna", timeout: int = 90) -> None:
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    def summarize(self, item: RawItem) -> SummaryResult:
        schema = {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "title": {"type": "string"},
                "description": {"type": "string"},
                "summary": {"type": "string"},
                "key_points": {"type": "array", "items": {"type": "string"}},
                "why_it_matters": {"type": "string"},
                "limitations": {"type": "string"},
                "tags": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["title", "description", "summary", "key_points", "why_it_matters", "limitations", "tags"],
        }
        content = {
            "domain": item.domain,
            "source": item.source_name,
            "title": item.title,
            "authors": item.authors,
            "published_at": item.published_at.isoformat(),
            "source_summary": item.summary[:12000],
            "original_url": item.url,
        }
        payload = {
            "model": self.model,
            "store": False,
            "reasoning": {"effort": "low"},
            "max_output_tokens": 1200,
            "instructions": (
                "你是严谨的量化研究编辑。只根据输入内容生成简体中文知识卡，不补造数字、实验、结论或背景。"
                "标题简短；描述回答新在哪里和为何有用；摘要区分事实与作者观点；局限必须明确证据边界。"
                "避免投资建议语气。"
            ),
            "input": json.dumps(content, ensure_ascii=False),
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "knowledge_card",
                    "strict": True,
                    "schema": schema,
                }
            },
        }
        request = urllib.request.Request(
            self.endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            result = json.loads(response.read())
        output_text = result.get("output_text") or self._find_output_text(result)
        card = json.loads(output_text)
        return SummaryResult(
            title=card["title"][:72],
            description=card["description"][:240],
            summary=card["summary"][:2400],
            key_points=card["key_points"][:5],
            why_it_matters=card["why_it_matters"][:600],
            limitations=card["limitations"][:600],
            tags=card["tags"][:6],
            ai_generated=True,
        )

    @staticmethod
    def _find_output_text(result: dict[str, Any]) -> str:
        for output in result.get("output", []):
            for content in output.get("content", []):
                if content.get("type") == "output_text" and content.get("text"):
                    return content["text"]
        raise ValueError("Responses API returned no output_text")


def configured_summarizer() -> Summarizer:
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        return SourceSummary()
    return OpenAIResponsesSummary(api_key, os.environ.get("OPENAI_MODEL", "gpt-5.6-luna"))
