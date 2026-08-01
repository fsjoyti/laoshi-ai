"""Tests for agent configuration and wiring."""

from unittest.mock import MagicMock, patch

import pytest
from langgraph.graph.state import CompiledStateGraph

from agent import SYSTEM_PROMPT, TOOLS, build_agent


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
            build_agent()

    def test_build_agent_raises_with_placeholder_key(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("OPENAI_API_KEY", "sk-your-key-here")
        with pytest.raises(ValueError, match="OPENAI_API_KEY"):
            build_agent()

    @patch("agent.ChatOpenAI")
    @patch("agent.create_agent")
    def test_build_agent_wires_graph_with_checkpointing(
        self,
        mock_create_agent: MagicMock,
        mock_chat_openai: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key-for-unit-tests")
        mock_graph = MagicMock(spec=CompiledStateGraph)
        mock_create_agent.return_value = mock_graph

        graph = build_agent(hsk_level="beginner")

        mock_chat_openai.assert_called_once()
        mock_create_agent.assert_called_once()
        call_kwargs = mock_create_agent.call_args.kwargs
        assert call_kwargs["tools"] == TOOLS
        assert "HSK Level: beginner" in call_kwargs["system_prompt"]
        assert call_kwargs["checkpointer"] is not None
        assert graph is mock_graph
