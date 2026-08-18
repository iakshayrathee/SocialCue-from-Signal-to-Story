"""Runtime configuration loaded from environment / .env."""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

# Load .env from the backend directory (if present). We do NOT override real
# environment variables, so an explicit MOCK_MODE / OPENAI_API_KEY passed via the
# shell or docker-compose `environment:` always wins over the .env file.
_BACKEND_DIR = Path(__file__).resolve().parent.parent
load_dotenv(_BACKEND_DIR / ".env", override=False)


def _as_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class Settings:
    """Small, explicit settings object. No magic."""

    def __init__(self) -> None:
        # MOCK_MODE defaults to TRUE so the app runs with zero API key / zero cost.
        self.mock_mode: bool = _as_bool(os.getenv("MOCK_MODE"), default=True)
        self.openai_api_key: str | None = os.getenv("OPENAI_API_KEY") or None
        self.openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

        # Directory that holds seed JSON data.
        self.data_dir: Path = Path(__file__).resolve().parent / "data"

        # Directory of built frontend static assets (populated in the Docker build).
        self.static_dir: Path = Path(
            os.getenv("STATIC_DIR", str(_BACKEND_DIR / "static"))
        )

    @property
    def use_real_llm(self) -> bool:
        """We only call OpenAI when explicitly out of mock mode AND a key exists."""
        return (not self.mock_mode) and bool(self.openai_api_key)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
