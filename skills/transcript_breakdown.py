"""Transcript breakdown skill: chunking, pinyin, simple polyphone resolution,
and vocabulary extraction.

This is an MVP implementation that avoids calling an LLM during tests. For
production-quality idiomatic translations and nuanced polyphone resolution,
wire the function to an LLM chain or improve the resolver heuristics.
"""

import re
from typing import List

from langchain_core.tools import tool
from pypinyin import Style, pinyin

from dictionary import format_lookup_results, get_cedict
from utils import chinese_to_pinyin

_SENTENCE_SPLIT_RE = re.compile(r"([^。！？\n]+[。！？]?)")


def _segment_text(text: str, granularity: str = "sentence") -> List[str]:
    if not text or not text.strip():
        return []

    if granularity == "paragraph":
        parts = [p.strip() for p in text.split("\n\n") if p.strip()]
        return parts

    # sentence-level (default): naive split on sentence punctuation
    parts = [m.group(1).strip() for m in _SENTENCE_SPLIT_RE.finditer(text)]
    # fallback if regex fails
    if not parts:
        parts = [p.strip() for p in re.split(r"[。！？\n]", text) if p.strip()]
    return parts


# Minimal polyphone resolver for a handful of common characters.
def _choose_polyphone(char: str, idx: int, text: str) -> str | None:
    # Provide forced tone-marked forms for simple contexts.
    # This is intentionally small — expand as needed.
    if char == "数":
        # 数学, 数量 -> shù, otherwise often shǔ (to count)
        if text[idx : idx + 2] in ("数学", "数量"):
            return "shù"
        return "shǔ"

    if char == "行":
        # 行业, 银行 -> háng ; otherwise xíng (to walk/do)
        if text[idx : idx + 2] in ("行业", "银行"):
            return "háng"
        return "xíng"

    if char == "重":
        # 重要, 重量 -> zhòng ; 重复 -> chóng
        if text[idx : idx + 2] in ("重要", "重量"):
            return "zhòng"
        if text[idx : idx + 2] == "重复":
            return "chóng"
        return None

    if char == "长":
        # 长期, 长城 -> cháng ; 校长 -> zhǎng
        if text[idx : idx + 2] in ("长期", "长城"):
            return "cháng"
        if text[idx : idx + 2] == "校长":
            return "zhǎng"
        return None

    return None


def _pinyin_with_polyphones(text: str) -> str:
    if not text:
        return ""

    # Get heteronym lists so we can pick an override if needed.
    syllables = pinyin(text, style=Style.TONE, heteronym=True, errors="default")
    out_parts: List[str] = []
    for idx, (char, py_opts) in enumerate(zip(text, syllables)):
        if not char.strip():
            continue
        forced = _choose_polyphone(char, idx, text)
        if forced:
            out_parts.append(forced)
            continue

        # If pypinyin returned options, pick the first one (common case)
        if py_opts and py_opts[0]:
            out_parts.append(py_opts[0])
        else:
            out_parts.append(char)

    # Join with spaces (aligns roughly with utils.chinese_to_pinyin)
    return " ".join(out_parts)


def _extract_vocab_candidates(chunk: str, max_items: int = 3) -> List[str]:
    """Extract up to `max_items` vocabulary candidates by checking CC-CEDICT hits.

    Simple greedy scan: try substrings of length 4..2 then 1.
    """
    cedict = get_cedict()
    seen: set[str] = set()
    results: List[str] = []
    n = len(chunk)
    for i in range(n):
        # try longer words first
        for L in (4, 3, 2, 1):
            if i + L > n:
                continue
            candidate = chunk[i : i + L]
            if candidate in seen or not candidate.strip():
                continue
            entries = cedict.lookup(candidate)
            if entries:
                seen.add(candidate)
                results.append(candidate)
                break
        if len(results) >= max_items:
            break

    return results


def breakdown_chinese_transcript(
    transcript_text: str,
    granularity: str = "sentence",
    include_vocab_notes: bool = True,
) -> str:
    """Break down `transcript_text` into annotated Markdown chunks.

    This MVP implementation produces tone-marked pinyin, a placeholder
    literal-ish translation built from dictionary hits, and simple vocab
    bullets using CC-CEDICT lookups. For idiomatic translations, wire an
    LLM-based chain in front of this tool.
    """
    chunks = _segment_text(transcript_text, granularity=granularity)
    if not chunks:
        return ""

    blocks: List[str] = []
    for idx, chunk in enumerate(chunks, start=1):
        header = f"### Chunk {idx}"
        chinese = f"**Chinese:**\n{chunk}"
        pinyin_text = _pinyin_with_polyphones(chunk)
        pinyin_block = f"**Pinyin:**\n{pinyin_text}"

        # Build a very small, dictionary-based fallback translation: join first
        # definitions for each extracted vocab item; this is NOT a substitute for
        # an LLM translation but suffices for structure and offline tests.
        vocab_candidates = _extract_vocab_candidates(chunk, max_items=4)
        cedict = get_cedict()
        translation_parts: List[str] = []
        for word in vocab_candidates:
            entries = cedict.lookup(word)
            if entries:
                # take the first definition from the first entry
                translation_parts.append(entries[0].definitions[0])

        translation = (
            "; ".join(translation_parts)
            if translation_parts
            else "(translation unavailable)"
        )
        translation_block = f"**Translation:**\n{translation}"

        vocab_lines: List[str] = []
        if include_vocab_notes and vocab_candidates:
            for word in vocab_candidates[:4]:
                entries = cedict.lookup(word)
                if entries:
                    pinyin_hdr = (
                        entries[0].pinyin
                        if entries[0].pinyin
                        else chinese_to_pinyin(word)
                    )
                    defs = "; ".join(entries[0].definitions[:2])
                    vocab_lines.append(f"* **{word}** (*{pinyin_hdr}*): {defs}")

        block_parts = [header, "", chinese, "", pinyin_block, "", translation_block]
        if vocab_lines:
            block_parts.append("")
            block_parts.extend(vocab_lines)

        blocks.append("\n".join(block_parts))

    return "\n\n".join(blocks)


# Register a StructuredTool for runtime/agent usage while keeping the
# callable function available for unit tests and local invocation.
breakdown_chinese_transcript_tool = tool(breakdown_chinese_transcript)
