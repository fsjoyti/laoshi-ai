"""Tests for CC-CEDICT parsing and lookup."""

from pathlib import Path

import pytest

from dictionary import CEDict, format_lookup_results, get_cedict, lookup_word


class TestCEDictParsing:
    def test_skips_comment_lines(self, sample_cedict_path: Path) -> None:
        cedict = CEDict(sample_cedict_path)
        assert cedict.lookup("你好")

    def test_lookup_simplified(self, sample_cedict_path: Path) -> None:
        cedict = CEDict(sample_cedict_path)
        entries = cedict.lookup("学校")
        assert len(entries) == 1
        assert entries[0].simplified == "学校"
        assert entries[0].traditional == "學校"
        assert entries[0].pinyin == "xue2 xiao4"
        assert "school" in entries[0].definitions

    def test_lookup_traditional(self, sample_cedict_path: Path) -> None:
        cedict = CEDict(sample_cedict_path)
        entries = cedict.lookup("學校")
        assert len(entries) == 1
        assert entries[0].simplified == "学校"

    def test_lookup_miss(self, sample_cedict_path: Path) -> None:
        cedict = CEDict(sample_cedict_path)
        assert cedict.lookup("不存在") == []

    def test_lookup_empty_query(self, sample_cedict_path: Path) -> None:
        cedict = CEDict(sample_cedict_path)
        assert cedict.lookup("") == []
        assert cedict.lookup("   ") == []

    def test_missing_file_raises(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError, match="CEDICT file not found"):
            CEDict(tmp_path / "missing.u8")


class TestFormatLookupResults:
    def test_no_entry_message(self) -> None:
        result = format_lookup_results("foo", [])
        assert result == "No CC-CEDICT entry found for 'foo'."


class TestLookupWordTool:
    def test_lookup_word_hit(self, cedict_env) -> None:
        result = lookup_word.invoke("你好")
        assert "hello" in result
        assert "ni3 hao3" in result

    def test_lookup_word_miss(self, cedict_env) -> None:
        result = lookup_word.invoke("notaword")
        assert "No CC-CEDICT entry found" in result

    def test_get_cedict_singleton(self, cedict_env) -> None:
        first = get_cedict()
        second = get_cedict()
        assert first is second
