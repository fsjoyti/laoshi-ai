"""QA tests (skeleton) for the transcript breakdown skill.

These tests are written TDD-style and mock external LLM dependencies where
appropriate. They assert the required Markdown structure and option handling.
"""

from typing import Any

import pytest

SAMPLE_TEXT = "你好，我叫王明。很高兴认识你。"


def _looks_like_markdown_breakdown(output: str) -> bool:
    """Basic structural checks for the Markdown output."""
    if not output:
        return False
    required = ["**Chinese:**", "**Pinyin:**", "**Translation:**"]
    return all(r in output for r in required)


def test_breakdown_returns_markdown_structure(monkeypatch: pytest.MonkeyPatch) -> None:
    """The tool should return a markdown-formatted breakdown containing required sections."""
    # Import the tool under test. Implementations should expose
    # `breakdown_chinese_transcript(transcript_text, granularity='sentence', include_vocab_notes=True)`
    try:
        from skills.transcript_breakdown import (
            breakdown_chinese_transcript,  # type: ignore
        )
    except Exception:
        pytest.skip("transcript_breakdown tool not implemented")

    # For test determinism, if the implementation internally calls an LLM or
    # a chain, the implementation should allow injection or monkeypatching of
    # that dependency. Tests can monkeypatch a `llm_invoke` helper if present.

    output = breakdown_chinese_transcript(SAMPLE_TEXT)
    assert _looks_like_markdown_breakdown(output)


def test_respects_include_vocab_notes_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    """When include_vocab_notes is False, vocabulary bullets should be omitted."""
    try:
        from skills.transcript_breakdown import (
            breakdown_chinese_transcript,  # type: ignore
        )
    except Exception:
        pytest.skip("transcript_breakdown tool not implemented")

    output = breakdown_chinese_transcript(SAMPLE_TEXT, include_vocab_notes=False)
    # Simple heuristic: no bulleted vocabulary lines starting with '* **'
    assert "* **" not in output


def test_pinyin_contains_tone_marks(monkeypatch: pytest.MonkeyPatch) -> None:
    """Pinyin output should include tone-marked vowels (ā á ǎ à)."""
    try:
        from skills.transcript_breakdown import (
            breakdown_chinese_transcript,  # type: ignore
        )
    except Exception:
        pytest.skip("transcript_breakdown tool not implemented")

    output = breakdown_chinese_transcript("你好")
    # Check for at least one common tone-marked vowel
    assert any(
        t in output for t in ["ā", "á", "ǎ", "à", "ǐ", "ǒ"]
    ), "No tone-marked vowels found in output"


# TODO: Add polyphone resolution tests once the resolver API is finalized.
