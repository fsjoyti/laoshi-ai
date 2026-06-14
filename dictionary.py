"""CC-CEDICT parser and dictionary lookup for the Chinese tutor agent."""

import os
import re
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.tools import tool

load_dotenv()

# CC-CEDICT line format: Traditional Simplified [pinyin] /definition1/definition2/
_CEDICT_LINE_PATTERN = re.compile(r"^(\S+)\s+(\S+)\s+\[([^\]]+)\]\s+(.+)$")


@dataclass(frozen=True)
class DictionaryEntry:
    """A single CC-CEDICT dictionary entry."""

    traditional: str
    simplified: str
    pinyin: str
    definitions: tuple[str, ...]


class CEDict:
    """Offline CC-CEDICT dictionary with lookup by simplified or traditional form."""

    def __init__(self, filepath: Path) -> None:
        self._filepath = filepath
        # Map headword (simplified or traditional) -> list of matching entries
        self._index: dict[str, list[DictionaryEntry]] = {}
        self._load()

    def _load(self) -> None:
        if not self._filepath.is_file():
            raise FileNotFoundError(
                f"CEDICT file not found at {self._filepath}. "
                "Download cedict_ts.u8 and set CEDICT_PATH in .env — see README.md."
            )

        with self._filepath.open(encoding="utf-8") as handle:
            for line in handle:
                entry = self._parse_line(line)
                if entry is None:
                    continue
                for headword in {entry.simplified, entry.traditional}:
                    self._index.setdefault(headword, []).append(entry)

    @staticmethod
    def _parse_line(line: str) -> DictionaryEntry | None:
        """Parse one CC-CEDICT line, skipping comments and malformed rows."""
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            return None

        match = _CEDICT_LINE_PATTERN.match(stripped)
        if not match:
            return None

        traditional, simplified, raw_pinyin, definitions_raw = match.groups()
        definitions = tuple(part for part in definitions_raw.split("/") if part)
        if not definitions:
            return None

        # CC-CEDICT stores numbered tones (ni3 hao3); keep as-is for accuracy.
        pinyin_text = raw_pinyin.strip()

        return DictionaryEntry(
            traditional=traditional,
            simplified=simplified,
            pinyin=pinyin_text,
            definitions=definitions,
        )

    def lookup(self, word: str) -> list[DictionaryEntry]:
        """Return all entries whose headword exactly matches the query."""
        query = word.strip()
        if not query:
            return []
        return list(self._index.get(query, []))


def _default_cedict_path() -> Path:
    env_path = os.getenv("CEDICT_PATH")
    if env_path:
        return Path(env_path)
    return Path(__file__).resolve().parent / "cedict_ts.u8"


_cedict: CEDict | None = None


def get_cedict() -> CEDict:
    """Return a lazily loaded singleton CEDict instance."""
    global _cedict
    if _cedict is None:
        _cedict = CEDict(_default_cedict_path())
    return _cedict


def format_lookup_results(word: str, entries: list[DictionaryEntry]) -> str:
    """Format dictionary hits as readable text for the agent."""
    if not entries:
        return f"No CC-CEDICT entry found for '{word}'."

    blocks: list[str] = []
    for index, entry in enumerate(entries, start=1):
        defs = "; ".join(entry.definitions)
        blocks.append(
            f"{index}. {entry.simplified} ({entry.traditional}) "
            f"[{entry.pinyin}] — {defs}"
        )
    return "\n".join(blocks)


@tool
def lookup_word(word: str) -> str:
    """
    Look up a Chinese word or character in the offline CC-CEDICT dictionary.

    Returns simplified/traditional forms, pinyin, and English definitions.
    Use this instead of guessing translations.
    """
    entries = get_cedict().lookup(word)
    return format_lookup_results(word, entries)
