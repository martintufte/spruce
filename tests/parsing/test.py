import pytest

from spruce.move.sequence import MoveSequence
from spruce.parsing import parse_steps


def test_parse_steps_returns_sequences() -> None:
    parsed = parse_steps("R U\nF2")

    assert parsed == [MoveSequence.from_str("R U"), MoveSequence.from_str("F2")]


def test_parse_steps_empty_input() -> None:
    parsed = parse_steps("")
    assert parsed == []


def test_parse_steps_rejects_skeleton_mode() -> None:
    with pytest.raises(
        ValueError,
        match=r"Definitions, substitutions, and skeleton syntax are not supported at line 1\.",
    ):
        parse_steps("-> R U R' U'")
