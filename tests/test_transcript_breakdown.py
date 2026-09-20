"""Tests for the transcript breakdown skill."""

from __future__ import annotations

import pytest

from skills.transcript_breakdown import (
    _format_pinyin_for_chunk,
    _pinyin_for_token,
    _segment_text,
    breakdown_chinese_transcript,
)

SAMPLE_TEXT = "你好，我叫王明。很高兴认识你。"
THREE_SENTENCES = "第一句。第二句。第三句很长，需要单独成块。"


def _looks_like_markdown_breakdown(output: str) -> bool:
    if not output:
        return False
    required = ["**Chinese:**", "**Pinyin:**", "**Translation:**"]
    return all(r in output for r in required)


def test_breakdown_returns_markdown_structure(cedict_env) -> None:
    output = breakdown_chinese_transcript(SAMPLE_TEXT, use_llm=False)
    assert _looks_like_markdown_breakdown(output)


def test_respects_include_vocab_notes_flag(cedict_env) -> None:
    output = breakdown_chinese_transcript(
        SAMPLE_TEXT, include_vocab_notes=False, use_llm=False
    )
    assert "* **" not in output


def test_pinyin_contains_tone_marks(cedict_env) -> None:
    output = breakdown_chinese_transcript("你好", use_llm=False)
    assert any(t in output for t in ["ā", "á", "ǎ", "à", "ǐ", "ǒ"])


def test_pinyin_omits_hyphenated_punctuation_noise() -> None:
    pinyin_line = _format_pinyin_for_chunk("你好，我")
    assert " - " not in pinyin_line
    assert "nǐ hǎo" in pinyin_line


def test_polyphone_resolution_in_token_pinyin() -> None:
    syllables = _pinyin_for_token("数学", "数学很重要", 0)
    assert "shù" in syllables


def test_proper_noun_pinyin_is_capitalized() -> None:
    pinyin_line = _format_pinyin_for_chunk("我叫王明。")
    assert "Wáng" in pinyin_line or "Míng" in pinyin_line


def test_vocab_uses_tone_marks_not_numeric_pinyin(cedict_env) -> None:
    output = breakdown_chinese_transcript("你好", use_llm=False)
    assert "ni3" not in output
    assert "hǎo" in output or "nǐ" in output


def test_sentence_chunking_splits_long_clauses() -> None:
    text = (
        "这是第一句。它很短。"
        "这个句子非常长，包含多个并列成分，而且应该被拆成更短的块来提高后续翻译质量。"
    )
    chunks = _segment_text(text, granularity="sentence")
    assert chunks[0].startswith("这是第一句。它很短")
    assert len(chunks) >= 2
    assert any("包含多个并列成分" in chunk for chunk in chunks)


def test_segment_text_limits_to_two_sentences_per_chunk() -> None:
    chunks = _segment_text(THREE_SENTENCES, granularity="sentence")
    assert len(chunks) >= 2
    for chunk in chunks:
        assert _segment_text(chunk) == [] or len(_segment_text(chunk)) <= 2


def test_offline_translation_is_not_a_misleading_word_salad(cedict_env) -> None:
    output = breakdown_chinese_transcript(SAMPLE_TEXT, use_llm=False)
    assert "hello; hi; good; I; me; my; to shout" not in output


def test_use_llm_flag_uses_mocked_translation(
    monkeypatch: pytest.MonkeyPatch, cedict_env
) -> None:
    import skills.transcript_breakdown as transcript_breakdown

    calls: list[tuple[str, list[str], str | None]] = []

    def fake_llm_translate(
        chunk: str, tokens: list[str], hsk_level: str | None = None
    ) -> str:
        calls.append((chunk, tokens, hsk_level))
        return "A mocked translation"

    monkeypatch.setattr(transcript_breakdown, "_llm_translate", fake_llm_translate)

    output = transcript_breakdown.breakdown_chinese_transcript(
        "你好", use_llm=True, hsk_level="beginner"
    )

    assert "A mocked translation" in output
    assert calls
    assert calls[0][2] == "beginner"


def test_use_llm_auto_disabled_without_api_key(
    monkeypatch: pytest.MonkeyPatch, cedict_env
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    output = breakdown_chinese_transcript("你好", use_llm=None)
    assert "A mocked translation" not in output
    assert "**Translation:**" in output
