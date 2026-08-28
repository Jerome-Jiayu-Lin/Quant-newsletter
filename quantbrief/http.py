from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any


USER_AGENT = "QuantBrief/0.1 (+https://github.com/Jerome-Jiayu-Lin/Quant-newsletter)"


@dataclass(slots=True)
class HttpResponse:
    status: int
    body: bytes
    headers: dict[str, str]


class HttpClient:
    """One HTTP seam for source identity, auth headers and durable response metadata."""

    def __init__(self, state_path: Path, timeout: int = 25) -> None:
        self.state_path = state_path
        self.timeout = timeout
        self.state: dict[str, dict[str, str]] = self._load_state()

    def _load_state(self) -> dict[str, dict[str, str]]:
        if not self.state_path.exists():
            return {}
        try:
            return json.loads(self.state_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}

    def save(self) -> None:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.state_path.write_text(
            json.dumps(self.state, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def get(self, url: str, *, accept: str = "*/*", headers: dict[str, str] | None = None) -> HttpResponse:
        request_headers = {"Accept": accept, "User-Agent": USER_AGENT}
        if headers:
            request_headers.update(headers)

        request = urllib.request.Request(url, headers=request_headers)
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                response_headers = {key.lower(): value for key, value in response.headers.items()}
                self.state[url] = {
                    key: value
                    for key, value in {
                        "etag": response_headers.get("etag", ""),
                        "last_modified": response_headers.get("last-modified", ""),
                    }.items()
                    if value
                }
                return HttpResponse(response.status, response.read(), response_headers)
        except urllib.error.HTTPError as error:
            if error.code == 304:
                return HttpResponse(304, b"", {})
            raise

    @staticmethod
    def github_headers() -> dict[str, str]:
        token = os.environ.get("GITHUB_TOKEN", "").strip()
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2026-03-10",
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers
