"""Tests for shared configuration helpers."""

from pathlib import Path

import pytest

from config import get_cedict_path, get_checkpoint_path, get_openai_api_key


def test_get_openai_api_key_raises_for_placeholder(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        get_openai_api_key()

    monkeypatch.setenv("OPENAI_API_KEY", "sk-your-key-here")
    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        get_openai_api_key()


def test_get_cedict_path_uses_project_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CEDICT_PATH", raising=False)
    path = get_cedict_path()
    assert path == Path(__file__).resolve().parent.parent / "cedict_ts.u8"


def test_get_checkpoint_path_uses_env_override(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    override = tmp_path / "checkpoints.sqlite"
    monkeypatch.setenv("CHECKPOINT_DB_PATH", str(override))
    assert get_checkpoint_path() == override
