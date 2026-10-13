"""Typed environment settings, with credentials excluded from diagnostics."""
from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class DemoConfig:
    searxng_base_url: str = "http://127.0.0.1:8080"
    openai_base_url: str | None = None
    openai_api_key: str | None = None
    openai_model: str | None = None
    openai_api_mode: str = "chat_completions"
    output_dir: str = "reports"

    @classmethod
    def from_env(cls) -> "DemoConfig":
        mode = os.getenv("OPENAI_API_MODE", "chat_completions").strip()
        if mode not in {"chat_completions", "responses"}:
            raise ValueError("OPENAI_API_MODE must be chat_completions or responses")
        return cls(
            searxng_base_url=os.getenv("SEARXNG_BASE_URL", "http://127.0.0.1:8080").rstrip("/"),
            openai_base_url=os.getenv("OPENAI_BASE_URL") or None,
            openai_api_key=os.getenv("OPENAI_API_KEY") or None,
            openai_model=os.getenv("OPENAI_MODEL") or None,
            openai_api_mode=mode,
            output_dir=os.getenv("DEMO_OUTPUT_DIR", "reports"),
        )

    def safe_diagnostic(self) -> dict[str, str | bool | None]:
        return {
            "searxng_base_url": self.searxng_base_url,
            "openai_base_url": self.openai_base_url,
            "openai_model": self.openai_model,
            "openai_api_mode": self.openai_api_mode,
            "openai_key_configured": bool(self.openai_api_key),
            "output_dir": self.output_dir,
        }
