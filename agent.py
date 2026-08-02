"""LangChain agent, tools, and checkpointed memory for the Chinese tutor."""

import truststore
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langgraph.graph.state import CompiledStateGraph

try:
    from langgraph.checkpoint.sqlite import SqliteSaver
except ImportError:  # pragma: no cover - compatibility fallback
    SqliteSaver = None

from config import get_checkpoint_path, get_openai_api_key
from dictionary import lookup_word
from hsk_selector import build_system_prompt
from utils import to_pinyin

truststore.inject_into_ssl()

TOOLS = [to_pinyin, lookup_word]

# Export a default SYSTEM_PROMPT for backward compatibility with tests.
SYSTEM_PROMPT = build_system_prompt(None)


def build_agent(hsk_level: str | None = None) -> CompiledStateGraph:
    """
    Create a LangGraph agent with durable checkpointed memory.

    Pass a stable ``thread_id`` in the invoke/stream config so each chat
    session keeps an isolated conversation history.
    The optional ``hsk_level`` adjusts the system prompt to match learner level.
    """
    api_key = get_openai_api_key()

    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0.5,
        api_key=api_key,
        streaming=True,
    )

    system_prompt = build_system_prompt(hsk_level)
    checkpoint_path = get_checkpoint_path()
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)

    if SqliteSaver is not None:
        checkpointer = SqliteSaver(str(checkpoint_path))
    else:
        from langgraph.checkpoint.memory import InMemorySaver

        checkpointer = InMemorySaver()

    return create_agent(
        model=llm,
        tools=TOOLS,
        system_prompt=system_prompt,
        checkpointer=checkpointer,
    )


# Backward-compatible alias used by chainlit_app and tests during migration.
build_agent_executor = build_agent
