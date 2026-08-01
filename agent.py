"""LangChain agent, tools, and checkpointed memory for the Chinese tutor."""

import os

import truststore
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph.state import CompiledStateGraph

from dictionary import lookup_word
from hsk_selector import build_system_prompt
from utils import to_pinyin

load_dotenv()
truststore.inject_into_ssl()

TOOLS = [to_pinyin, lookup_word]

# Export a default SYSTEM_PROMPT for backward compatibility with tests.
SYSTEM_PROMPT = build_system_prompt(None)


def build_agent(hsk_level: str | None = None) -> CompiledStateGraph:
    """
    Create a LangGraph agent with short-term memory via InMemorySaver.

    Pass a stable ``thread_id`` in the invoke/stream config so each chat
    session keeps an isolated conversation history.
    The optional ``hsk_level`` adjusts the system prompt to match learner level.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "sk-your-key-here":
        raise ValueError(
            "OPENAI_API_KEY is not set. Copy .env.example to .env and add your key."
        )

    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0.5,
        api_key=api_key,
        streaming=True,
    )

    system_prompt = build_system_prompt(hsk_level)

    return create_agent(
        model=llm,
        tools=TOOLS,
        system_prompt=system_prompt,
        checkpointer=InMemorySaver(),
    )


# Backward-compatible alias used by chainlit_app and tests during migration.
build_agent_executor = build_agent
