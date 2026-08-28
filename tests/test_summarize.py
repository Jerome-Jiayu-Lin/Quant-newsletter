from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from quantbrief.summarize import (
    DeepSeekChatSummary,
    OpenAIResponsesSummary,
    SourceSummary,
    configured_summarizer,
)


class SummarizerConfigurationTests(unittest.TestCase):
    def configured(self, **values: str):
        clean = {
            "SUMMARY_PROVIDER": "",
            "OPENAI_API_KEY": "",
            "DEEPSEEK_API_KEY": "",
            "OPENAI_MODEL": "",
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


if __name__ == "__main__":
    unittest.main()
