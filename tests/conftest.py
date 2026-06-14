"""Shared pytest fixtures."""

from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_cedict_path() -> Path:
    return FIXTURES / "sample_cedict.u8"


@pytest.fixture
def cedict_env(sample_cedict_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Point CEDICT at the sample file and reset the lazy singleton."""
    import dictionary

    monkeypatch.setenv("CEDICT_PATH", str(sample_cedict_path))
    dictionary._cedict = None
    yield sample_cedict_path
    dictionary._cedict = None
