"""Pinyin conversion utilities for the Chinese tutor agent."""

from langchain_core.tools import tool
from pypinyin import Style, pinyin


def chinese_to_pinyin(text: str) -> str:
    """
    Convert Chinese text to tone-marked pinyin using pypinyin.

    Non-Chinese characters are preserved inline; Chinese characters are
    converted to syllables with tone marks (e.g. nǐ hǎo).
    """
    if not text or not text.strip():
        return ""

    syllables = pinyin(text, style=Style.TONE, heteronym=False, errors="default")
    parts: list[str] = []

    for char, py_list in zip(text, syllables):
        if py_list and py_list[0]:
            parts.append(py_list[0])
        elif char.strip():
            parts.append(char)

    return " ".join(parts)


@tool
def to_pinyin(chinese_text: str) -> str:
    """
    Convert Chinese text to pinyin with tone marks.

    Use this tool whenever you need accurate pronunciation for Chinese
    characters or phrases (e.g. before presenting them to the student).
    """
    return chinese_to_pinyin(chinese_text)
