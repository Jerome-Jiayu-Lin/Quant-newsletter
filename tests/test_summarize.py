from __future__ import annotations

import json
import os
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from quantbrief.models import RawItem
from quantbrief.summarize import (
    DeepSeekChatSummary,
    OpenAIResponsesSummary,
    SourceSummary,
    configured_summarizer,
)


class FakeResponse:
    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self) -> bytes:
        return json.dumps(self.payload, ensure_ascii=False).encode("utf-8")


def raw_item() -> RawItem:
    now = datetime(2026, 8, 28, tzinfo=timezone.utc)
    return RawItem(
        source_id="arxiv",
        source_name="arXiv",
        source_group="论文",
        domain="量化研究",
        title="A Factor Study",
        url="https://example.com/paper",
        summary="We test a factor with out-of-sample data.",
        published_at=now,
        retrieved_at=now,
    )


class SummarizerConfigurationTests(unittest.TestCase):
    def configured(self, **values: str):
        clean = {
            "SUMMARY_PROVIDER": "",
            "OPENAI_API_KEY": "",
            "DEEPSEEK_API_KEY": "",
            "OPENAI_MODEL": "",
            "OPENAI_BASE_URL": "",
            "DEEPSEEK_MODEL": "",
            "DEEPSEEK_BASE_URL": "",
        }
        clean.update(values)
        with patch.dict(os.environ, clean, clear=False):
            return configured_summarizer()

    def test_no_key_uses_source_summary(self) -> None:
        self.assertIsInstance(self.configured(), SourceSummary)

    def test_auto_uses_deepseek_when_it_is_the_only_key(self) -> None:
        summarizer = self.configured(DEEPSEEK_API_KEY="test-key")
        self.assertIsInstance(summarizer, DeepSeekChatSummary)
        self.assertEqual(summarizer.endpoint, "https://api.deepseek.com/chat/completions")

    def test_explicit_provider_overrides_auto_priority(self) -> None:
        summarizer = self.configured(
            SUMMARY_PROVIDER="deepseek",
            OPENAI_API_KEY="openai-key",
            DEEPSEEK_API_KEY="deepseek-key",
            DEEPSEEK_MODEL="deepseek-v4-pro",
        )
        self.assertIsInstance(summarizer, DeepSeekChatSummary)
        self.assertEqual(summarizer.model, "deepseek-v4-pro")

    def test_auto_prefers_openai_when_both_keys_exist(self) -> None:
        summarizer = self.configured(OPENAI_API_KEY="openai-key", DEEPSEEK_API_KEY="deepseek-key")
        self.assertIsInstance(summarizer, OpenAIResponsesSummary)

    def test_explicit_provider_requires_its_key(self) -> None:
        with self.assertRaisesRegex(ValueError, "requires DEEPSEEK_API_KEY"):
            self.configured(SUMMARY_PROVIDER="deepseek")

    def test_require_ai_rejects_source_only_mode(self) -> None:
        clean = {"SUMMARY_PROVIDER": "auto", "OPENAI_API_KEY": "", "DEEPSEEK_API_KEY": ""}
        with patch.dict(os.environ, clean, clear=False):
            with self.assertRaisesRegex(ValueError, "AI summary is required"):
                configured_summarizer(require_ai=True)

    def test_openai_base_url_is_configurable(self) -> None:
        summarizer = self.configured(
            SUMMARY_PROVIDER="openai",
            OPENAI_API_KEY="test-key",
            OPENAI_BASE_URL="https://gateway.example/v1/",
        )
        self.assertIsInstance(summarizer, OpenAIResponsesSummary)
        self.assertEqual(summarizer.endpoint, "https://gateway.example/v1/responses")


class ProviderResponseTests(unittest.TestCase):
    card = {
        "title": "因子研究",
        "description": "样本外检验一个因子。",
        "summary": "作者使用样本外数据检验因子表现。",
        "key_points": ["包含样本外检验"],
        "why_it_matters": "有助于判断稳健性。",
        "limitations": "尚未核验全文。",
        "tags": ["因子"],
    }

    def test_openai_structured_response_is_normalized(self) -> None:
        payload = {"output_text": json.dumps(self.card, ensure_ascii=False)}
        with patch("urllib.request.urlopen", return_value=FakeResponse(payload)) as request:
            result = OpenAIResponsesSummary("test-key").summarize(raw_item())
        self.assertEqual(result.title, "因子研究")
        self.assertEqual(result.provider, "openai")
        sent = json.loads(request.call_args.args[0].data)
        self.assertEqual(sent["text"]["format"]["type"], "json_schema")

    def test_deepseek_json_response_is_normalized(self) -> None:
        payload = {"choices": [{"message": {"content": json.dumps(self.card, ensure_ascii=False)}}]}
        with patch("urllib.request.urlopen", return_value=FakeResponse(payload)) as request:
            result = DeepSeekChatSummary("test-key").summarize(raw_item())
        self.assertEqual(result.title, "因子研究")
        self.assertEqual(result.provider, "deepseek")
        sent = json.loads(request.call_args.args[0].data)
        self.assertEqual(sent["response_format"], {"type": "json_object"})


if __name__ == "__main__":
    unittest.main()
