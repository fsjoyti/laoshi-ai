"""Transcript breakdown skill: chunking, pinyin, vocabulary, and translation."""

from __future__ import annotations

import os
import re
from typing import List

from langchain_core.tools import tool
from pypinyin import Style, pinyin

try:
    import jieba
except Exception:  # pragma: no cover - optional dependency
    jieba = None

try:
    from langchain_core.messages import HumanMessage, SystemMessage
    from langchain_openai import ChatOpenAI
except Exception:  # pragma: no cover - optional runtime
    ChatOpenAI = None
    HumanMessage = None
    SystemMessage = None

from dictionary import get_cedict
from utils import chinese_to_pinyin

_SENTENCE_SPLIT_RE = re.compile(r"[^。！？\n]+(?:[。！？]|$)")
_MAX_CHUNK_CHARS = 80
_SHORT_CHUNK_TOTAL = 60
_MAX_SENTENCES_PER_CHUNK = 2
_CJK_RE = re.compile(r"[\u4e00-\u9fff]")
_PUNCT_ONLY_RE = re.compile(r"^[\s，。！？、；：,.!?;:\-—…]+$")
_NAME_PREFIX_RE = re.compile(r"(我叫|叫作|叫|是|姓)([\u4e00-\u9fff]{2,4})")
_OFFLINE_TRANSLATION_HINT = (
    "(Idiomatic translation requires an API key; enable `use_llm` when "
    "`OPENAI_API_KEY` is configured.)"
)


def _is_cjk(char: str) -> bool:
    return "\u4e00" <= char <= "\u9fff"


def _openai_api_key_or_none() -> str | None:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key or api_key == "sk-your-key-here":
        return None
    return api_key


def _llm_translation_enabled(use_llm: bool | None) -> bool:
    if use_llm is False:
        return False
    if use_llm is True:
        return _openai_api_key_or_none() is not None
    return _openai_api_key_or_none() is not None


def _split_sentences(text: str) -> List[str]:
    """Split text into sentence-like units while preserving punctuation."""
    if not text or not text.strip():
        return []

    parts = [m.group(0).strip() for m in _SENTENCE_SPLIT_RE.finditer(text)]
    return [p for p in parts if p]


def _sentence_count(text: str) -> int:
    sentences = _split_sentences(text)
    return len(sentences) if sentences else (1 if text.strip() else 0)


def _split_long_chunk(chunk: str) -> List[str]:
    """Split a long chunk into shorter chunks at clause boundaries if possible."""
    stripped = chunk.strip()
    if not stripped:
        return []

    if len(stripped) <= _MAX_CHUNK_CHARS:
        return [stripped]

    parts = re.split(r"([，；：,;:])", stripped)
    if len(parts) > 2:
        pieces: List[str] = []
        current = ""
        for part in parts:
            if not part:
                continue
            if part in {"，", "；", "：", ",", ";", ":"}:
                if current:
                    current += part
                continue
            if current:
                current += part
            else:
                current = part
            if len(current) >= _MAX_CHUNK_CHARS * 0.7:
                pieces.append(current.strip())
                current = ""
        if current:
            pieces.append(current.strip())
        pieces = [p for p in pieces if p]
        if len(pieces) > 1:
            return pieces

    pieces = []
    start = 0
    while start < len(stripped):
        end = min(len(stripped), start + _MAX_CHUNK_CHARS // 2)
        pieces.append(stripped[start:end].strip())
        start = end
    return [p for p in pieces if p]


def _segment_text(text: str, granularity: str = "sentence") -> List[str]:
    if not text or not text.strip():
        return []

    if granularity == "paragraph":
        parts = [p.strip() for p in text.split("\n\n") if p.strip()]
        return parts

    parts = _split_sentences(text)
    if not parts:
        return [p.strip() for p in re.split(r"[。！？\n]", text) if p.strip()]

    merged: List[str] = []
    current = ""
    for part in parts:
        if not current:
            current = part
            continue

        combined = f"{current}{part}"
        if (
            _sentence_count(current) < _MAX_SENTENCES_PER_CHUNK
            and len(combined) <= _SHORT_CHUNK_TOTAL
        ):
            current = combined
        else:
            merged.append(current)
            current = part

    if current:
        merged.append(current)

    result: List[str] = []
    for chunk in merged:
        result.extend(_split_long_chunk(chunk))
    return result


def _choose_polyphone(char: str, idx: int, text: str) -> str | None:
    if char == "数":
        if text[idx : idx + 2] in ("数学", "数量"):
            return "shù"
        return "shǔ"

    if char == "行":
        if text[idx : idx + 2] in ("行业", "银行"):
            return "háng"
        return "xíng"

    if char == "重":
        if text[idx : idx + 2] in ("重要", "重量"):
            return "zhòng"
        if text[idx : idx + 2] == "重复":
            return "chóng"
        return None

    if char == "长":
        if text[idx : idx + 2] in ("长期", "长城"):
            return "cháng"
        if text[idx : idx + 2] == "校长":
            return "zhǎng"
        return None

    return None


def _proper_noun_ranges(chunk: str) -> list[tuple[int, int]]:
    return [(match.start(2), match.end(2)) for match in _NAME_PREFIX_RE.finditer(chunk)]


def _token_in_proper_noun_range(
    token_start: int, token_end: int, ranges: list[tuple[int, int]]
) -> bool:
    return any(token_start >= start and token_end <= end for start, end in ranges)


def _capitalize_syllables(pinyin_text: str) -> str:
    parts = []
    for syllable in pinyin_text.split():
        if not syllable:
            continue
        parts.append(syllable[0].upper() + syllable[1:] if syllable else syllable)
    return " ".join(parts)


def _pinyin_for_token(token: str, chunk: str, token_start: int) -> str:
    if not token.strip():
        return ""
    if _PUNCT_ONLY_RE.match(token):
        return token.strip()

    if not _CJK_RE.search(token):
        return token

    syllables: List[str] = []
    for offset, char in enumerate(token):
        if not _is_cjk(char):
            syllables.append(char)
            continue
        idx = token_start + offset
        forced = _choose_polyphone(char, idx, chunk)
        if forced:
            syllables.append(forced)
            continue
        py = pinyin(char, style=Style.TONE, heteronym=False, errors="default")
        syllables.append(py[0][0] if py and py[0] else char)

    joined = " ".join(syllables)
    token_end = token_start + len(token)
    if _token_in_proper_noun_range(token_start, token_end, _proper_noun_ranges(chunk)):
        return _capitalize_syllables(joined)
    return joined


def _format_pinyin_for_chunk(chunk: str) -> str:
    """Tone-marked pinyin with polyphones, readable punctuation, name capitalization."""
    tokens = _segment_words(chunk)
    if not tokens:
        return _pinyin_with_polyphones(chunk)

    parts: List[str] = []
    cursor = 0
    for token in tokens:
        token_start = chunk.find(token, cursor)
        if token_start < 0:
            token_start = cursor

        if _PUNCT_ONLY_RE.match(token):
            punct = token.strip()
            if parts:
                parts[-1] = f"{parts[-1]}{punct}"
            else:
                parts.append(punct)
        else:
            parts.append(_pinyin_for_token(token, chunk, token_start))

        cursor = token_start + len(token)

    return " ".join(part for part in parts if part)


def _pinyin_with_polyphones(text: str) -> str:
    if not text:
        return ""

    syllables = pinyin(text, style=Style.TONE, heteronym=True, errors="default")
    out_parts: List[str] = []
    for idx, (char, py_opts) in enumerate(zip(text, syllables)):
        if not char.strip():
            continue
        forced = _choose_polyphone(char, idx, text)
        if forced:
            out_parts.append(forced)
            continue
        if py_opts and py_opts[0]:
            out_parts.append(py_opts[0])
        else:
            out_parts.append(char)

    return " ".join(out_parts)


def _segment_words(text: str) -> List[str]:
    if not text:
        return []
    if jieba is not None:
        try:
            tokens = jieba.lcut(text)
            return [t.strip() for t in tokens if t.strip()]
        except Exception:
            pass

    tokens: List[str] = []
    buf = ""
    for ch in text:
        if _is_cjk(ch):
            if buf:
                tokens.append(buf)
                buf = ""
            tokens.append(ch)
        else:
            buf += ch
    if buf:
        tokens.append(buf)
    return tokens


def _llm_translate(
    chunk: str, tokens: List[str], hsk_level: str | None = None
) -> str | None:
    if ChatOpenAI is None or HumanMessage is None or SystemMessage is None:
        return None
    api_key = _openai_api_key_or_none()
    if not api_key:
        return None

    level_hint = (
        f" Target learner level: {hsk_level}."
        if hsk_level
        else " Target learner level: general Mandarin learner."
    )
    system = (
        "You are an expert Chinese-to-English translator for language learners. "
        "Return exactly one natural, idiomatic English sentence for the Chinese "
        f"passage.{level_hint} Do not add quotes or commentary."
    )
    user = f"Chinese: {chunk}\nTokens: {' | '.join(tokens)}\nEnglish translation:"

    try:
        llm = ChatOpenAI(model="gpt-4o", temperature=0.2, api_key=api_key)
        response = llm.invoke(
            [SystemMessage(content=system), HumanMessage(content=user)]
        )
        content = getattr(response, "content", None)
        if isinstance(content, str) and content.strip():
            return content.strip()
    except Exception:
        return None
    return None


def _extract_vocab_candidates(chunk: str, max_items: int = 4) -> List[str]:
    try:
        cedict = get_cedict()
    except FileNotFoundError:
        return []

    candidates: List[str] = []
    seen: set[str] = set()

    for token in sorted(_segment_words(chunk), key=len, reverse=True):
        if not _CJK_RE.search(token) or len(token) < 2:
            continue
        if token in seen:
            continue
        if cedict.lookup(token):
            seen.add(token)
            candidates.append(token)
        if len(candidates) >= max_items:
            return candidates

    n = len(chunk)
    for length in (4, 3, 2):
        for i in range(n):
            if i + length > n:
                continue
            candidate = chunk[i : i + length]
            if not _CJK_RE.search(candidate) or candidate in seen:
                continue
            if cedict.lookup(candidate):
                seen.add(candidate)
                candidates.append(candidate)
            if len(candidates) >= max_items:
                return candidates

    return candidates[:max_items]


def _dictionary_gloss_translation(vocab_candidates: List[str], cedict) -> str | None:
    if cedict is None or not vocab_candidates:
        return None

    phrases: List[str] = []
    for word in vocab_candidates[:2]:
        entries = cedict.lookup(word)
        if not entries:
            continue
        gloss = entries[0].definitions[0]
        phrases.append(f"{word}: {gloss}")

    if not phrases:
        return None
    return "Key terms — " + "; ".join(phrases)


def _vocab_pinyin_display(word: str) -> str:
    return _pinyin_with_polyphones(word) or chinese_to_pinyin(word)


def breakdown_chinese_transcript(
    transcript_text: str,
    granularity: str = "sentence",
    include_vocab_notes: bool = True,
    use_llm: bool | None = None,
    hsk_level: str | None = None,
) -> str:
    """Break down `transcript_text` into annotated Markdown chunks."""
    chunks = _segment_text(transcript_text, granularity=granularity)
    if not chunks:
        return ""

    want_llm = _llm_translation_enabled(use_llm)
    blocks: List[str] = []

    for idx, chunk in enumerate(chunks, start=1):
        header = f"### Chunk {idx}"
        chinese = f"**Chinese:**\n{chunk}"
        pinyin_block = f"**Pinyin:**\n{_format_pinyin_for_chunk(chunk)}"

        tokens = [t for t in _segment_words(chunk) if _CJK_RE.search(t)]
        vocab_candidates = _extract_vocab_candidates(chunk, max_items=4)
        try:
            cedict = get_cedict()
        except FileNotFoundError:
            cedict = None

        translation = _OFFLINE_TRANSLATION_HINT
        if want_llm:
            llm_translation = _llm_translate(chunk, tokens, hsk_level=hsk_level)
            if llm_translation:
                translation = llm_translation

        if translation == _OFFLINE_TRANSLATION_HINT:
            gloss = _dictionary_gloss_translation(vocab_candidates, cedict)
            if gloss:
                translation = gloss

        translation_block = f"**Translation:**\n{translation}"

        vocab_lines: List[str] = []
        if include_vocab_notes and vocab_candidates and cedict is not None:
            for word in vocab_candidates[:4]:
                entries = cedict.lookup(word)
                if entries:
                    pinyin_hdr = _vocab_pinyin_display(word)
                    defs = "; ".join(entries[0].definitions[:2])
                    vocab_lines.append(f"* **{word}** (*{pinyin_hdr}*): {defs}")

        block_parts = [header, "", chinese, "", pinyin_block, "", translation_block]
        if vocab_lines:
            block_parts.append("")
            block_parts.extend(vocab_lines)

        blocks.append("\n".join(block_parts))

    return "\n\n".join(blocks)


breakdown_chinese_transcript_tool = tool(breakdown_chinese_transcript)
