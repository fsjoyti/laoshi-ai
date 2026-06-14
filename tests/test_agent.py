"""Tests for agent configuration and wiring."""

from unittest.mock import MagicMock, patch

import pytest

from agent import SYSTEM_PROMPT, TOOLS, build_agent_executor


class TestAgentConfig:
    def test_system_prompt_requires_pinyin_format(self) -> None:
        assert "你好 (nǐ hǎo)" in SYSTEM_PROMPT
        assert "lookup_word" in SYSTEM_PROMPT
        assert "to_pinyin" in SYSTEM_PROMPT

    def test_tools_registered(self) -> None:
        tool_names = {tool.name for tool in TOOLS}
        assert tool_names == {"to_pinyin", "lookup_word"}

    def test_build_agent_raises_without_api_key(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        with pytest.raises(ValueError, match="OPENAI_API_KEY"):
            build_agent_executor()

    def test_build_agent_raises_with_placeholder_key(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("OPENAI_API_KEY", "sk-your-key-here")
        with pytest.raises(ValueError, match="OPENAI_API_KEY"):
            build_agent_executor()

    @patch("agent.ChatOpenAI")
    def test_build_agent_wires_executor(
        self, mock_chat_openai: MagicMock, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key-for-unit-tests")
        executor = build_agent_executor()
        mock_chat_openai.assert_called_once()
        assert len(executor.tools) == 2
        assert executor.memory is not None
