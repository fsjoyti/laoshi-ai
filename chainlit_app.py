"""Chainlit UI for the Chinese language learning tutor."""

import asyncio
import logging
import uuid

import chainlit as cl
from langchain_core.messages import AIMessage, HumanMessage

from agent import build_agent

logger = logging.getLogger(__name__)

GREETING = (
    "你好 (nǐ hǎo)! Welcome — I'm your Chinese tutor.\n\n"
    "Ask me how to say something, practice a phrase, or get gentle "
    "corrections on your Chinese. I'll explain in English and always "
    "show pinyin with tone marks, like: 谢谢 (xièxie).\n\n"
    "What would you like to learn today?"
)

HSK_ACTIONS = [
    cl.Action(name="hsk_beginner", payload={"level": "beginner"}, label="Beginner"),
    cl.Action(
        name="hsk_intermediate", payload={"level": "intermediate"}, label="Intermediate"
    ),
    cl.Action(name="hsk_skip", payload={"level": ""}, label="No preference"),
]


def _get_or_create_agent():
    """Build the agent synchronously (safe to run in a worker thread)."""
    hsk_level = cl.user_session.get("hsk_level")
    return build_agent(hsk_level=hsk_level or None)


def _agent_config() -> dict:
    """Stable thread id for LangGraph checkpointing within this chat session."""
    thread_id = cl.user_session.get("agent_thread_id")
    if not thread_id:
        thread_id = str(uuid.uuid4())
        cl.user_session.set("agent_thread_id", thread_id)
    return {"configurable": {"thread_id": thread_id}}


async def _prompt_hsk_level() -> None:
    """Ask the learner to pick an HSK level once per chat session."""
    if cl.user_session.get("hsk_prompt_done"):
        return

    cl.user_session.set("hsk_prompt_done", True)
    res = await cl.AskActionMessage(
        content="Choose your level so I can tailor explanations:",
        actions=HSK_ACTIONS,
    ).send()

    if res and res.get("payload", {}).get("level"):
        level = res["payload"]["level"]
        cl.user_session.set("hsk_level", level)
        cl.user_session.set("agent", None)
        await cl.Message(
            content=f"Got it — I'll teach at **{level}** level. Ask me anything!"
        ).send()


async def _prompt_tools() -> None:
    """Offer a simple tools menu (visible button) so users notice available actions."""
    if cl.user_session.get("tools_prompt_done"):
        return

    cl.user_session.set("tools_prompt_done", True)
    tools_actions = [
        cl.Action(name="open_tools", payload={}, label="Open tools"),
    ]

    res = await cl.AskActionMessage(
        content=(
            "Try built-in tools (e.g. Transcript breakdown). "
            "Click 'Open tools' for usage info."
        ),
        actions=tools_actions,
    ).send()

    # If the user clicked the tools button, provide a quick usage hint.
    if res:
        await cl.Message(
            content=(
                "Transcript breakdown: paste or type a Chinese passage prefixed with "
                "`breakdown:`\n"
                "Example: `breakdown: 你好，我叫李雷。`"
            )
        ).send()


@cl.on_chat_start
async def on_chat_start() -> None:
    """Greet the student and offer an HSK level picker."""
    await cl.Message(content=GREETING).send()
    await _prompt_hsk_level()
    await _prompt_tools()


@cl.on_message
async def on_message(message: cl.Message) -> None:
    """Route the user's message through the LangChain agent with streaming."""
    txt_lower = (message.content or "").strip().lower()
    if txt_lower.startswith("level:"):
        level = txt_lower.split(":", 1)[1].strip()
        if level in ("beginner", "intermediate"):
            cl.user_session.set("hsk_level", level)
            cl.user_session.set("agent", None)
            await cl.Message(
                content=f"HSK level set to **{level}**. Starting fresh for this level."
            ).send()
            return
        await cl.Message(
            content="Unknown level. Use `level: beginner` or `level: intermediate`."
        ).send()
        return

    if txt_lower.startswith("breakdown:"):
        # Extract text after the prefix and call the breakdown tool synchronously.
        raw = message.content.split(":", 1)[1].strip()
        if not raw:
            await cl.Message(content="Please provide text after `breakdown:`").send()
            return

        try:
            # import at call-time to ensure the symbol is available in the
            # running Chainlit process (avoids 'name not defined' errors).
            from skills.transcript_breakdown import breakdown_chinese_transcript

            result = await asyncio.to_thread(breakdown_chinese_transcript, raw)
            await cl.Message(content=result).send()
        except Exception as exc:
            logger.exception("Transcript breakdown failed")
            await cl.Message(content=f"Transcript breakdown error: {exc}").send()
        return

    agent = cl.user_session.get("agent")

    if agent is None:
        try:
            agent = await asyncio.to_thread(_get_or_create_agent)
            cl.user_session.set("agent", agent)
        except ValueError as exc:
            await cl.Message(content=f"Configuration error: {exc}").send()
            return
        except Exception as exc:
            logger.exception("Failed to initialize agent")
            await cl.Message(
                content=(
                    "Could not start the tutor. Check that `.env` contains a valid "
                    f"`OPENAI_API_KEY`.\n\nDetails: {exc}"
                )
            ).send()
            return

    response_msg = cl.Message(content="")
    await response_msg.send()

    input_state = {"messages": [HumanMessage(content=message.content)]}
    config = _agent_config()
    streamed_any = False

    try:
        async for msg, _metadata in agent.astream(
            input_state,
            config=config,
            stream_mode="messages",
        ):
            if not isinstance(msg, AIMessage):
                continue
            chunk = msg.content
            if isinstance(chunk, str) and chunk:
                await response_msg.stream_token(chunk)
                streamed_any = True
            elif isinstance(chunk, list):
                for part in chunk:
                    text = part.get("text", "") if isinstance(part, dict) else str(part)
                    if text:
                        await response_msg.stream_token(text)
                        streamed_any = True

        if not streamed_any:
            result = await asyncio.to_thread(agent.invoke, input_state, config)
            messages = result.get("messages", [])
            if messages and isinstance(messages[-1], AIMessage):
                fallback = (messages[-1].content or "").strip()
                if fallback:
                    await response_msg.stream_token(fallback)
                    streamed_any = True

        if not streamed_any or not response_msg.content.strip():
            response_msg.content = "I couldn't generate a response. Please try again."

        await response_msg.update()
    except TimeoutError:
        await response_msg.remove()
        await cl.Message(
            content="The tutor took too long to respond. Please try again."
        ).send()
    except Exception as exc:
        logger.exception("Agent stream failed")
        await response_msg.remove()
        await cl.Message(
            content=(
                "Sorry, I couldn't reach the language model. "
                "Check your internet connection and OpenAI API key.\n\n"
                f"Details: {exc}"
            )
        ).send()
