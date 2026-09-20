"""Sprint 3 QA: pronunciation feedback via mocked TTS (no network)."""

from __future__ import annotations

import pytest


def _import_pronunciation():
    try:
        from skills import (
            pronunciation_tts as tts_module,  # type: ignore[import-not-found]
        )
    except ImportError:
        pytest.skip("skills.pronunciation_tts not implemented (Sprint 3)")
    return tts_module


class TestPronunciationFeedback:
    def test_build_feedback_includes_pinyin_and_hints(self) -> None:
        tts = _import_pronunciation()
        feedback = tts.build_pronunciation_feedback("你好")

        assert "你好" in feedback.chinese
        assert feedback.pinyin
        assert len(feedback.hints) == 3
        assert all(hint.strip() for hint in feedback.hints)

    def test_empty_phrase_raises(self) -> None:
        tts = _import_pronunciation()
        with pytest.raises(ValueError, match="empty"):
            tts.build_pronunciation_feedback("   ")

    def test_synthesize_uses_injected_client(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        tts = _import_pronunciation()
        calls: list[str] = []

        class FakeTTSClient:
            def synthesize(self, text: str) -> bytes:
                calls.append(text)
                return b"FAKE-AUDIO"

        monkeypatch.setattr(tts, "get_tts_client", lambda: FakeTTSClient())

        audio = tts.synthesize_mandarin("谢谢")

        assert audio == b"FAKE-AUDIO"
        assert calls == ["谢谢"]
