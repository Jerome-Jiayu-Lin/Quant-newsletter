from __future__ import annotations

import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from quantbrief.cli import load_env_file


class EnvironmentFileTests(unittest.TestCase):
    def test_loads_values_without_overwriting_process_environment(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / ".env.local"
            path.write_text("SUMMARY_PROVIDER=deepseek\nDEEPSEEK_API_KEY='local-key'\n", encoding="utf-8")
            with patch.dict(os.environ, {"SUMMARY_PROVIDER": "openai"}, clear=False):
                os.environ.pop("DEEPSEEK_API_KEY", None)
                load_env_file(path)
                self.assertEqual(os.environ["SUMMARY_PROVIDER"], "openai")
                self.assertEqual(os.environ["DEEPSEEK_API_KEY"], "local-key")
                os.environ.pop("DEEPSEEK_API_KEY", None)

    def test_rejects_invalid_environment_keys(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / ".env.local"
            path.write_text("NOT-A-KEY=value\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "invalid environment key"):
                load_env_file(path)


if __name__ == "__main__":
    unittest.main()
