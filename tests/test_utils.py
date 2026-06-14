"""Tests for pinyin conversion utilities."""

from utils import chinese_to_pinyin, to_pinyin


class TestChineseToPinyin:
    def test_basic_greeting(self) -> None:
        result = chinese_to_pinyin("你好")
        assert "n" in result  # tone-marked nǐ
        assert "h" in result  # tone-marked hǎo
        assert len(result.split()) == 2

    def test_empty_input(self) -> None:
        assert chinese_to_pinyin("") == ""
        assert chinese_to_pinyin("   ") == ""

    def test_mixed_text_preserves_non_chinese(self) -> None:
        result = chinese_to_pinyin("A你好")
        assert "A" in result


class TestToPinyinTool:
    def test_tool_invocation(self) -> None:
        result = to_pinyin.invoke("学校")
        assert result
        assert len(result.split()) >= 2
