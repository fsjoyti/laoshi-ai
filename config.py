"""Shared configuration helpers for secrets, paths, and persistence settings."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def get_openai_api_key() -> str:
    """Return the configured OpenAI API key or raise a helpful error."""
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key or api_key == "sk-your-key-here":
        raise ValueError(
            "OPENAI_API_KEY is not set. Copy .env.example to .env and add your key."
        )
    return api_key


def get_cedict_path() -> Path:
    """Resolve the CC-CEDICT path from the environment or the project root."""
    env_path = os.getenv("CEDICT_PATH", "").strip()
    if env_path:
        return Path(env_path).expanduser().resolve()
    return Path(__file__).resolve().parent / "cedict_ts.u8"


def get_checkpoint_path() -> Path:
    """Resolve the LangGraph checkpoint database path.

    Reads `CHECKPOINT_DB_PATH` from the environment or falls back to a
    `checkpoints.sqlite` file in the project root.
    """
    env_path = os.getenv("CHECKPOINT_DB_PATH", "").strip()
    if env_path:
        return Path(env_path).expanduser().resolve()
    return Path(__file__).resolve().parent / "checkpoints.sqlite"
