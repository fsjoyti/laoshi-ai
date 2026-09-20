"""Sprint 3 QA: durable checkpoint persistence and thread isolation."""

from __future__ import annotations

import pytest
from langchain.agents import create_agent
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.checkpoint.memory import InMemorySaver

from config import get_checkpoint_path


def _sqlite_saver(db_path):
    try:
        from langgraph.checkpoint.sqlite import SqliteSaver
    except ImportError:
        return None
    return SqliteSaver(str(db_path))


class TestCheckpointConfiguration:
    def test_default_checkpoint_path_is_sqlite_file(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("CHECKPOINT_DB_PATH", raising=False)
        path = get_checkpoint_path()
        assert path.name == "checkpoints.sqlite"
        assert path.suffix == ".sqlite"


class TestThreadIsolation:
    def test_separate_thread_ids_keep_isolated_histories(self) -> None:
        llm = GenericFakeChatModel(
            messages=iter(
                [
                    AIMessage(content="reply-a1"),
                    AIMessage(content="reply-b1"),
                ]
            )
        )
        checkpointer = InMemorySaver()
        agent = create_agent(
            model=llm,
            tools=[],
            system_prompt="Test tutor",
            checkpointer=checkpointer,
        )
        config_a = {"configurable": {"thread_id": "thread-a"}}
        config_b = {"configurable": {"thread_id": "thread-b"}}

        agent.invoke({"messages": [HumanMessage(content="hello A")]}, config_a)
        agent.invoke({"messages": [HumanMessage(content="hello B")]}, config_b)

        snapshot_a = agent.get_state(config_a)
        snapshot_b = agent.get_state(config_b)

        assert len(snapshot_a.values["messages"]) == 2
        assert len(snapshot_b.values["messages"]) == 2
        assert snapshot_a.values["messages"][0].content == "hello A"
        assert snapshot_b.values["messages"][0].content == "hello B"


class TestRestartPersistence:
    def test_sqlite_checkpointer_survives_new_agent_instance(
        self, tmp_path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Simulates process restart: new agent + same DB file + same thread_id."""
        db_path = tmp_path / "restart.sqlite"
        saver_cls = _sqlite_saver(db_path)
        if saver_cls is None:
            pytest.skip(
                "langgraph-checkpoint-sqlite not installed — "
                "required for restart persistence AC"
            )

        llm = GenericFakeChatModel(
            messages=iter(
                [
                    AIMessage(content="first-turn"),
                    AIMessage(content="second-turn"),
                ]
            )
        )
        config = {"configurable": {"thread_id": "persist-thread"}}

        agent_before = create_agent(
            model=llm,
            tools=[],
            system_prompt="Test tutor",
            checkpointer=saver_cls,
        )
        agent_before.invoke(
            {"messages": [HumanMessage(content="Remember this thread")]},
            config,
        )

        agent_after = create_agent(
            model=llm,
            tools=[],
            system_prompt="Test tutor",
            checkpointer=_sqlite_saver(db_path),
        )
        state = agent_after.get_state(config)

        assert len(state.values["messages"]) >= 2
        assert state.values["messages"][0].content == "Remember this thread"

    def test_in_memory_checkpointer_does_not_survive_new_instance(self) -> None:
        """Documents why SQLite (or external store) is required for restart AC."""
        llm = GenericFakeChatModel(messages=iter([AIMessage(content="only-once")]))
        config = {"configurable": {"thread_id": "volatile-thread"}}

        agent_before = create_agent(
            model=llm,
            tools=[],
            system_prompt="Test tutor",
            checkpointer=InMemorySaver(),
        )
        agent_before.invoke(
            {"messages": [HumanMessage(content="volatile")]},
            config,
        )

        agent_after = create_agent(
            model=llm,
            tools=[],
            system_prompt="Test tutor",
            checkpointer=InMemorySaver(),
        )
        state = agent_after.get_state(config)

        assert state.values == {}
