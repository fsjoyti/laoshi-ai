from hsk_selector import build_system_prompt


def test_build_system_prompt_default():
    p = build_system_prompt(None)
    assert "You are a patient, encouraging Chinese language tutor" in p
    assert "HSK Level:" not in p


def test_build_system_prompt_beginner():
    p = build_system_prompt("beginner")
    assert "HSK Level: beginner" in p
    assert "short sentences" in p


def test_build_system_prompt_intermediate():
    p = build_system_prompt("intermediate")
    assert "HSK Level: intermediate" in p
    assert "richer vocabulary" in p
