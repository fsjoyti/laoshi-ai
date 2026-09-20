"""Sprint 3 QA: interactive quiz generation and grading (no live LLM)."""

from __future__ import annotations

import pytest


def _import_quiz():
    try:
        from skills import quiz as quiz_module  # type: ignore[import-not-found]
    except ImportError:
        pytest.skip("skills.quiz not implemented (Sprint 3)")
    return quiz_module


SAMPLE_QUESTIONS = [
    {
        "prompt": "What does 你好 mean?",
        "choices": ["Hello", "Goodbye", "Thank you", "Sorry"],
        "answer_index": 0,
    },
    {
        "prompt": "Choose the pinyin for 谢谢",
        "choices": ["xièxie", "nǐ hǎo", "zàijiàn", "duìbuqǐ"],
        "answer_index": 0,
    },
]


class TestQuizGeneration:
    def test_generate_quiz_respects_count_and_hsk_level(self) -> None:
        quiz = _import_quiz()
        pack = quiz.generate_quiz(hsk_level="beginner", num_questions=2)

        assert len(pack.questions) == 2
        assert pack.hsk_level == "beginner"
        assert all(q.choices for q in pack.questions)

    def test_generate_quiz_rejects_invalid_hsk_level(self) -> None:
        quiz = _import_quiz()
        with pytest.raises(ValueError, match="hsk"):
            quiz.generate_quiz(hsk_level="expert", num_questions=1)


class TestQuizGrading:
    def test_grade_quiz_returns_score_and_feedback(self) -> None:
        quiz = _import_quiz()
        pack = quiz.QuizPack(
            hsk_level="beginner",
            questions=[quiz.QuizQuestion(**q) for q in SAMPLE_QUESTIONS],
        )
        answers = [0, 1]  # second answer wrong

        result = quiz.grade_quiz(pack, answers)

        assert result.score == 50
        assert len(result.feedback) == 2
        assert "incorrect" in result.feedback[1].lower()

    def test_grade_quiz_validates_answer_length(self) -> None:
        quiz = _import_quiz()
        pack = quiz.generate_quiz(hsk_level="beginner", num_questions=2)

        with pytest.raises(ValueError, match="answers"):
            quiz.grade_quiz(pack, [0])
