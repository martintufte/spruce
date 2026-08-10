import pytest

from spruce.configuration.enumeration import Puzzle
from spruce.move.meta import MoveMeta
from spruce.move.sequence import MoveSequence
from spruce.parsing import parse_steps

MOVE_META = MoveMeta.from_puzzle(puzzle=Puzzle._3x3x3)


def test_parse_steps_returns_sequences() -> None:
    parsed = parse_steps("R U\nF2", move_meta=MOVE_META)

    assert parsed == [MoveSequence.from_str("R U"), MoveSequence.from_str("F2")]


def test_parse_steps_empty_input() -> None:
    parsed = parse_steps("", move_meta=MOVE_META)
    assert parsed == []


def test_parse_steps_rejects_skeleton_mode() -> None:
    with pytest.raises(
        ValueError,
        match=r"Definitions, substitutions, and skeleton syntax are not supported at line 1\.",
    ):
        parse_steps("-> R U R' U'", move_meta=MOVE_META)
