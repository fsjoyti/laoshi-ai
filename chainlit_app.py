"""Chainlit UI for the Chinese language learning tutor."""

import asyncio
import logging

import chainlit as cl

from agent import build_agent_executor

logger = logging.getLogger(__name__)

GREETING = (
    "你好 (nǐ hǎo)! Welcome — I'm your Chinese tutor.\n\n"
    "Ask me how to say something, practice a phrase, or get gentle "
    "corrections on your Chinese. I'll explain in English and always "
    "show pinyin with tone marks, like: 谢谢 (xièxie).\n\n"
    "What would you like to learn today?"
)


def _get_or_create_agent():
    """Build the agent synchronously (safe to run in a worker thread)."""
    # Read the user's HSK level preference from the Chainlit session (if set)
    hsk_level = cl.user_session.get("hsk_level")
    return build_agent_executor(hsk_level=hsk_level)


@cl.on_chat_start
async def on_chat_start() -> None:
    """Greet the student immediately; build the agent on first message."""
    await cl.Message(content=GREETING).send()


@cl.on_message
async def on_message(message: cl.Message) -> None:
    """Route the user's message through the LangChain agent."""
    # allow the user to set their HSK level by sending messages like:
    #  "level: beginner"  or  "level: intermediate"
    txt_lower = (message.content or "").strip().lower()
    if txt_lower.startswith("level:"):
        level = txt_lower.split(":", 1)[1].strip()
        if level in ("beginner", "intermediate"):
            cl.user_session.set("hsk_level", level)
            # force rebuild of the agent so the new prompt takes effect
            cl.user_session.set("agent_executor", None)
            await cl.Message(content=f"HSK level set to {level}. Rebuilding session...").send()
            return
        else:
            await cl.Message(content="Unknown level. Use 'level: beginner' or 'level: intermediate'.").send()
            return

    agent_executor = cl.user_session.get("agent_executor")

    if agent_executor is None:
        try:
            agent_executor = await asyncio.to_thread(_get_or_create_agent)
            cl.user_session.set("agent_executor", agent_executor)
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

    try:
        response = await asyncio.wait_for(
            asyncio.to_thread(agent_executor.invoke, {"input": message.content}),
            timeout=120,
        )
        output = (response.get("output") or "").strip()
        if not output:
            output = "I couldn't generate a response. Please try again."
        await cl.Message(content=output).send()
    except TimeoutError:
        await cl.Message(
            content="The tutor took too long to respond. Please try again."
        ).send()
    except Exception as exc:
        logger.exception("Agent invoke failed")
        await cl.Message(
            content=(
                "Sorry, I couldn't reach the language model. "
                "Check your internet connection and OpenAI API key.\n\n"
                f"Details: {exc}"
            )
        ).send()
