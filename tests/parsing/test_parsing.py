import pytest

from spruce.parsing import parse_generator
from spruce.parsing import parse_scramble
from spruce.parsing import parse_steps
from spruce.puzzle.cube.group import build_move_meta
from spruce.puzzle.cube.notation import parse_moves
from spruce.puzzle.cube.spec import Puzzle

MOVE_META = build_move_meta(puzzle=Puzzle._3x3x3)


def test_parse_steps_returns_sequences() -> None:
    parsed = parse_steps("R U\nF2", move_meta=MOVE_META)

    assert parsed == [parse_moves("R U"), parse_moves("F2")]


def test_parse_steps_empty_input() -> None:
    parsed = parse_steps("", move_meta=MOVE_META)
    assert parsed == []


def test_parse_steps_rejects_skeleton_mode() -> None:
    with pytest.raises(
        ValueError,
        match=r"Definitions, substitutions, and skeleton syntax are not supported at line 1\.",
    ):
        parse_steps("-> R U R' U'", move_meta=MOVE_META)


# Syntactically valid notation that is not a move of a 3x3x3
WRONG_PUZZLE_SYMBOL = "3Rw"


def test_parse_steps_rejects_symbol_of_another_puzzle() -> None:
    """Test that a well formed step is still rejected when the puzzle lacks the symbol."""
    with pytest.raises(ValueError, match=r"Invalid moves entered at line 2\."):
        parse_steps(f"R U\nF2 {WRONG_PUZZLE_SYMBOL}", move_meta=MOVE_META)


def test_parse_scramble_returns_sequence() -> None:
    assert parse_scramble("R U R'", move_meta=MOVE_META) == parse_moves("R U R'")


def test_parse_scramble_rejects_symbol_of_another_puzzle() -> None:
    with pytest.raises(ValueError, match=r"Unknown move symbols \['3Rw'\]"):
        parse_scramble(f"R {WRONG_PUZZLE_SYMBOL} U", move_meta=MOVE_META)


def test_parse_scramble_rejects_inverse_moves() -> None:
    with pytest.raises(ValueError, match="Inverse moves for scramble is not supported"):
        parse_scramble("R (U)", move_meta=MOVE_META)


def test_parse_generator_returns_symbols() -> None:
    assert parse_generator("<M, U>", move_meta=MOVE_META) == frozenset({"M", "U"})


def test_parse_generator_rejects_unknown_symbol() -> None:
    """Test that a symbol built from legal characters is still rejected."""
    with pytest.raises(ValueError, match=r"Unknown move symbols \['RRR'\]"):
        parse_generator("<RRR, U>", move_meta=MOVE_META)


def test_parse_generator_rejects_illegal_characters() -> None:
    with pytest.raises(ValueError, match="Invalid symbols entered!"):
        parse_generator("<banana>", move_meta=MOVE_META)


def test_parse_generator_rejects_missing_brackets() -> None:
    with pytest.raises(ValueError, match="Invalid move generator format!"):
        parse_generator("U, R, F", move_meta=MOVE_META)
