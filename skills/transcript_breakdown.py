"""Transcript breakdown skill: chunking, pinyin, simple polyphone resolution,
and vocabulary extraction.

This is an MVP implementation that avoids calling an LLM during tests. For
production-quality idiomatic translations and nuanced polyphone resolution,
wire the function to an LLM chain or improve the resolver heuristics.
"""

import os
import re
from typing import List

from langchain_core.tools import tool
from pypinyin import Style, pinyin

# Optional tokenizer for better pinyin grouping
try:
    import jieba
except Exception:  # pragma: no cover - optional dependency
    jieba = None

# Optional LLM client
try:
    from langchain_openai import ChatOpenAI
except Exception:  # pragma: no cover - optional runtime
    ChatOpenAI = None

from dictionary import get_cedict
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


def _segment_words(text: str) -> List[str]:
    """Segment Chinese text into words using `jieba` when available.

    Falls back to per-character tokens if `jieba` is not installed.
    """
    if not text:
        return []
    if jieba is not None:
        try:
            tokens = jieba.lcut(text)
            tokens = [t.strip() for t in tokens if t.strip()]
            return tokens
        except Exception:
            pass
    # Fallback: return each CJK character as a token, preserve ASCII runs
    tokens: List[str] = []
    buf = ""
    for ch in text:
        # Basic check for CJK Unified Ideographs
        if "\u4e00" <= ch <= "\u9fff":
            if buf:
                tokens.append(buf)
                buf = ""
            tokens.append(ch)
        else:
            buf += ch
    if buf:
        tokens.append(buf)
    return tokens


def _tokens_to_pinyin(tokens: List[str]) -> str:
    """Convert a list of tokens to hyphenated pinyin with tone marks.

    Each token's characters are joined with spaces, tokens joined with hyphens.
    """
    parts: List[str] = []
    for token in tokens:
        if not token.strip():
            continue
        # For ASCII tokens, preserve as-is
        if all(ord(c) < 128 for c in token):
            parts.append(token)
            continue
        syls = pinyin(token, style=Style.TONE, heteronym=False, errors="default")
        flattened = " ".join(s[0] if s else token for s in syls)
        parts.append(flattened)
    return " - ".join(parts)


def _llm_translate(
    chunk: str, tokens: List[str], hsk_level: str | None = None
) -> str | None:
    """Use an LLM to produce an idiomatic translation for a chunk.

    Returns the translation string or None if no LLM is available.
    """
    if ChatOpenAI is None:
        return None
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key or api_key == "sk-your-key-here":
        return None

    # Build a concise prompt asking for a single-sentence idiomatic translation.
    system = (
        "You are an expert Chinese->English translator. "
        "Provide a single-sentence, idiomatic English translation for the given "
        "Chinese text."
    )
    # Include tokenized form to help with pinyin grouping
    user = (
        f"Chinese: {chunk}\n"
        f"Tokens: {' | '.join(tokens)}\n"
        "Respond only with the single-sentence English translation."
    )

    try:
        llm = ChatOpenAI(model="gpt-4o", temperature=0.2, api_key=api_key)
        resp = llm.generate(
            [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ]
        )
        # langchain_openai ChatOpenAI.generate returns a complex object;
        # try to extract text
        text = None
        try:
            text = resp.generations[0][0].text
        except Exception:
            try:
                text = str(resp)
            except Exception:
                text = None
        if text:
            return text.strip()
    except Exception:
        return None
    return None


def _extract_vocab_candidates(chunk: str, max_items: int = 3) -> List[str]:
    """Extract up to `max_items` vocabulary candidates by checking CC-CEDICT hits.

    Simple greedy scan: try substrings of length 4..2 then 1.
    """
    try:
        cedict = get_cedict()
    except FileNotFoundError:
        # CC-CEDICT not available (CI or minimal environment) — skip vocab.
        return []
    seen: set[str] = set()
    results: List[str] = []
    n = len(chunk)
    for i in range(n):
        # try longer words first
        for length in (4, 3, 2, 1):
            if i + length > n:
                continue
            candidate = chunk[i : i + length]
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
    use_llm: bool = False,
) -> str:
    """Break down `transcript_text` into annotated Markdown chunks.

    This MVP implementation produces tone-marked pinyin, a placeholder
    literal-ish translation built from dictionary hits, and simple vocab
    bullets using CC-CEDICT lookups. When `use_llm=True`, it will prefer an
    LLM-based translation when one is available.
    """
    chunks = _segment_text(transcript_text, granularity=granularity)
    if not chunks:
        return ""

    blocks: List[str] = []
    for idx, chunk in enumerate(chunks, start=1):
        header = f"### Chunk {idx}"
        chinese = f"**Chinese:**\n{chunk}"
        # Prefer token-aware pinyin when jieba is available; fall back to
        # character-level pinyin with simple polyphone resolution.
        tokens = _segment_words(chunk)
        token_pinyin = _tokens_to_pinyin(tokens)
        if token_pinyin:
            pinyin_block = f"**Pinyin:**\n{token_pinyin}"
        else:
            pinyin_text = _pinyin_with_polyphones(chunk)
            pinyin_block = f"**Pinyin:**\n{pinyin_text}"

        # Build a very small, dictionary-based fallback translation: join first
        # definitions for each extracted vocab item; this is NOT a substitute for
        # an LLM translation but suffices for structure and offline tests.
        vocab_candidates = _extract_vocab_candidates(chunk, max_items=4)
        try:
            cedict = get_cedict()
        except FileNotFoundError:
            cedict = None
        translation = "(translation unavailable)"
        if use_llm:
            llm_translation = _llm_translate(chunk, tokens)
            if llm_translation:
                translation = llm_translation
        if translation == "(translation unavailable)":
            translation_parts: List[str] = []
            for word in vocab_candidates:
                if cedict is None:
                    break
                entries = cedict.lookup(word)
                if entries:
                    # take the first definition from the first entry
                    translation_parts.append(entries[0].definitions[0])

            if translation_parts:
                translation = "; ".join(translation_parts)

        translation_block = f"**Translation:**\n{translation}"

        vocab_lines: List[str] = []
        if include_vocab_notes and vocab_candidates and cedict is not None:
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
