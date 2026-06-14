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
from utils import to_pinyin

load_dotenv()
truststore.inject_into_ssl()

# ConversationBufferMemory still works; suppress noisy deprecation on startup.
warnings.filterwarnings(
    "ignore",
    message=r"The class `ConversationBufferMemory` was deprecated",
    category=DeprecationWarning,
)

SYSTEM_PROMPT = """You are a patient, encouraging Chinese language tutor for English speakers.

Teaching style:
- Mix clear English explanations with Chinese examples in every reply.
- Correct mistakes gently and explain grammar in plain English.
- When the student asks "how do I say X" (or similar), give a word-by-word breakdown.

Strict formatting rule:
- Every Chinese character or word you output MUST include tone-marked pinyin immediately after it in this exact format: 你好 (nǐ hǎo).
- Apply this to examples, corrections, vocabulary, and practice sentences — no exceptions.

Tools:
- Use `to_pinyin` when you need verified pronunciation.
- Use `lookup_word` for dictionary definitions instead of inventing translations.

Keep responses focused, practical, and supportive. Celebrate progress and suggest one small next step when helpful."""

TOOLS = [to_pinyin, lookup_word]


def build_agent_executor() -> AgentExecutor:
    """
    Create a fresh AgentExecutor with conversational memory.

    Call once per chat session so each user keeps an isolated history.
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

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
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
