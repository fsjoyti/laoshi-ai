"""LangChain agent, tools, and memory configuration for the Chinese tutor."""

import os
import warnings

import truststore
from dotenv import load_dotenv

# LangChain v1 moved the classic agent API to langchain-classic.
from langchain_classic.agents import AgentExecutor, create_tool_calling_agent
from langchain_classic.memory import ConversationBufferMemory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

from dictionary import lookup_word
from hsk_selector import build_system_prompt
from utils import to_pinyin

load_dotenv()
truststore.inject_into_ssl()

# ConversationBufferMemory still works; suppress noisy deprecation on startup.
warnings.filterwarnings(
    "ignore",
    message=r"The class `ConversationBufferMemory` was deprecated",
    category=DeprecationWarning,
)

TOOLS = [to_pinyin, lookup_word]

# Export a default SYSTEM_PROMPT for backward compatibility with tests.
SYSTEM_PROMPT = build_system_prompt(None)


def build_agent_executor(hsk_level: str | None = None) -> AgentExecutor:
    """
    Create a fresh AgentExecutor with conversational memory.

    Call once per chat session so each user keeps an isolated history.
    The optional `hsk_level` adjusts the system prompt to match learner level.
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
    )

    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True,
    )

    # Compose the final system prompt, possibly augmented for HSK level.
    system_prompt = build_system_prompt(hsk_level)

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ]
    )

    agent = create_tool_calling_agent(llm, TOOLS, prompt)

    return AgentExecutor(
        agent=agent,
        tools=TOOLS,
        memory=memory,
        verbose=True,
        handle_parsing_errors=True,
    )
