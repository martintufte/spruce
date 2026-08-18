import pytest

from spruce.move.meta import MoveMeta
from spruce.move.sequence import MoveSequence
from spruce.move.sequence import cleanup
from spruce.move.sequence import invert
from spruce.move.sequence import measure
from spruce.move.sequence import reduce
from spruce.move.sequence import shift_rotations_to_end
from spruce.move.sequence import unniss
from spruce.puzzle.cube.metrics import Metric
from spruce.puzzle.cube.spec import Puzzle


class TestMoveSequenceBasics:
    """Test basic MoveSequence construction and operations."""

    def test_empty_initialization(self) -> None:
        """Test empty sequence initialization."""
        seq = MoveSequence()
        assert len(seq) == 0
        assert str(seq) == "None"
        assert not seq

    def test_string_initialization(self) -> None:
        """Test initialization from string."""
        seq = MoveSequence.from_str("R U R' U'")
        assert len(seq) == 4
        assert seq.normal == ["R", "U", "R'", "U'"]
        assert seq.inverse == []

    def test_list_initialization(self) -> None:
        """Test initialization from list."""
        seq = MoveSequence.from_str("R U R' U'")
        assert len(seq) == 4
        assert seq.normal == ["R", "U", "R'", "U'"]
        assert seq.inverse == []

    def test_string_representation(self) -> None:
        """Test string representation."""
        seq = MoveSequence.from_str("R U R' U'")
        assert str(seq) == "R U R' U'"
        assert repr(seq) == "MoveSequence.from_str(\"R U R' U'\")"

    def test_equality(self) -> None:
        """Test equality comparison."""
        seq1 = MoveSequence.from_str("R U R' U'")
        seq2 = MoveSequence.from_str("R U R' U'")
        seq3 = MoveSequence.from_str("R U")
        assert seq1 == seq2
        assert seq1 != seq3

    def test_addition(self) -> None:
        """Test sequence concatenation."""
        seq1 = MoveSequence.from_str("R U")
        seq2 = MoveSequence.from_str("R' U'")
        result = seq1 + seq2
        assert result == MoveSequence.from_str("R U R' U'")

    def test_multiplication(self) -> None:
        """Test sequence repetition."""
        seq = MoveSequence.from_str("R U")
        result = seq * 3
        assert result == MoveSequence.from_str("R U R U R U")

    def test_sides_are_kept_separate(self) -> None:
        """Test that normal and inverse moves stay on their own side."""
        seq = MoveSequence.from_str("R U (R' U')")
        assert seq.normal == ["R", "U"]
        assert seq.inverse == ["R'", "U'"]
        assert len(seq) == 4

    def test_comparison_operators(self) -> None:
        """Test length comparison operators."""
        seq1 = MoveSequence.from_str("R U")
        seq2 = MoveSequence.from_str("R U R'")
        seq3 = MoveSequence.from_str("R U")
        assert seq1 < seq2
        assert seq1 <= seq2
        assert seq1 <= seq3
        assert seq2 > seq1
        assert seq2 >= seq1
        assert seq1 >= seq3

    def test_hash(self) -> None:
        """Test hashing for use in sets/dicts."""
        seq1 = MoveSequence.from_str("R U")
        seq2 = MoveSequence.from_str("R U")
        seq3 = MoveSequence.from_str("R U'")
        assert hash(seq1) == hash(seq2)
        assert hash(seq1) != hash(seq3)

    def test_copy(self) -> None:
        """Test copying a sequence."""
        seq = MoveSequence.from_str("R U R' U'")
        seq_copy = seq.__copy__()
        assert seq == seq_copy
        assert seq.normal is not seq_copy.normal
        assert seq.inverse is not seq_copy.inverse


@pytest.mark.parametrize(
    ("moves", "expected"),
    [
        ("", ""),
        ("x2 y2", "z2"),
        ("y2 z2", "x2"),
        ("z2 x2", "y2"),
        ("x y2 z' x' y2 x2 z' y' x y2 x' z2 y' x2 z' y2", "y"),
    ],
)
def test_canonicalize_rotations(moves: str, expected: str) -> None:
    """Test that rotations are combined and moved to end."""
    seq = MoveSequence.from_str(moves)
    move_meta = MoveMeta.from_puzzle(puzzle=Puzzle._3x3x3)

    shift_rotations_to_end(seq, move_meta=move_meta, canonicalize=True)
    assert seq == MoveSequence.from_str(expected)


@pytest.mark.parametrize(
    ("moves", "expected"),
    [
        ("x L", "L x"),
        ("x F", "D x"),
        ("x y2 z' x' y2 x2 z' y' x y2 x' z2 y' x2 z' y2 F", "R y"),
    ],
)
def test_shift_rotations_to_end_with_canonicalization(moves: str, expected: str) -> None:
    """Test that rotations are combined and moved to end."""
    seq = MoveSequence.from_str(moves)
    move_meta = MoveMeta.from_puzzle(puzzle=Puzzle._3x3x3)

    shift_rotations_to_end(seq, move_meta=move_meta, canonicalize=True)
    assert seq == MoveSequence.from_str(expected)


@pytest.mark.parametrize(
    ("move", "expected"),
    [
        ("", ""),
        ("R R", "R2"),
        ("R R'", ""),
        ("R R R R", ""),
        ("Rw L' R Rw", "L' R Rw2"),
        ("L F Rw2 Rw2 F' L", "L2"),
        ("R U R' U'", "R U R' U'"),
    ],
)
def test_reduce(move: str, expected: str) -> None:
    """Test that reduce works for non-rotations."""
    seq = MoveSequence.from_str(move)
    move_meta = MoveMeta.from_puzzle(puzzle=Puzzle._3x3x3)

    reduce(seq, move_meta)
    assert seq == MoveSequence.from_str(expected)


@pytest.mark.parametrize(
    ("move", "expected"),
    [
        ("", ""),
        ("Lw", "R x'"),
        ("Rw", "L x"),
        ("Fw", "B z"),
        ("Bw", "F z'"),
        ("Uw", "D y"),
        ("Dw", "U y'"),
    ],
)
def test_replace_wide_moves_3x3(move: str, expected: str) -> None:
    """Test wide move replacement for 3x3 cube."""
    seq = MoveSequence.from_str(move)
    move_meta = MoveMeta.from_puzzle(puzzle=Puzzle._3x3x3)

    seq.apply(move_meta.substitute)
    assert seq == MoveSequence.from_str(expected)


@pytest.mark.parametrize(
    ("move", "expected"),
    [
        ("", ""),
        ("Lw", "Lw"),
        ("3Rw", "3Rw"),
        ("4Fw", "4Fw"),
        ("5Bw", "4Fw z'"),
        ("6Uw", "3Dw y"),
        ("7Dw", "Uw y'"),
        ("8Lw", "R x'"),
    ],
)
def test_replace_wide_moves_9x9(move: str, expected: str) -> None:
    """Test wide move replacement for 9x9 cube."""
    seq = MoveSequence.from_str(move)
    move_meta = MoveMeta.from_puzzle(Puzzle._9x9x9)

    seq.apply(move_meta.substitute)
    assert seq == MoveSequence.from_str(expected)


# TODO: This fails now because the wide moves outside the range is not seen in the permutations
@pytest.mark.xfail
@pytest.mark.parametrize(
    ("move", "expected"),
    [
        ("", ""),
        ("3Lw", "x'"),
        ("4Rw", "x"),
        ("5Fw", "z"),
        ("6Bw", "z'"),
        ("7Uw", "y"),
        ("8Dw", "y'"),
    ],
)
def test_replace_wide_moves_outside_range(move: str, expected: str) -> None:
    """Test wide moves that exceed cube size convert to rotations."""
    seq = MoveSequence.from_str(move)
    move_meta = MoveMeta.from_puzzle(puzzle=Puzzle._3x3x3)

    seq.apply(move_meta.substitute)
    assert seq == MoveSequence.from_str(expected)


@pytest.mark.parametrize(
    ("move", "expected"),
    [
        ("M", "L' R x'"),
        ("E", "U D' y'"),
        ("S", "F' B z"),
        ("M'", "L R' x"),
        ("M2", "L2 R2 x2"),
    ],
)
def test_replace_slice_moves(move: str, expected: str) -> None:
    """Test slice move replacement."""
    seq = MoveSequence.from_str(move)
    move_meta = MoveMeta.from_puzzle(puzzle=Puzzle._3x3x3)

    seq.apply(move_meta.substitute)
    assert seq == MoveSequence.from_str(expected)


def test_unniss() -> None:
    """Test unnissing a sequence."""
    seq = MoveSequence.from_str("R U (R' U')")
    move_meta = MoveMeta.from_puzzle(puzzle=Puzzle._3x3x3)

    result = unniss(seq, move_meta)
    assert result == MoveSequence.from_str("R U U R")


def test_measure() -> None:
    """Test measuring sequence length."""
    seq = MoveSequence.from_str("R U R' U'")
    assert measure(seq, Metric.HTM) == 4


def test_cleanup() -> None:
    """Test sequence cleanup combines operations."""
    seq = MoveSequence.from_str("(R') L M' (S2) x2 (z)")
    move_meta = MoveMeta.from_puzzle(puzzle=Puzzle._3x3x3)

    result = cleanup(seq, move_meta)
    assert result == MoveSequence.from_str("L2 R' x' (R' F2 B2 z')")


def test_invert() -> None:
    """Test sequence inversion reverses and inverts each move."""
    seq = MoveSequence.from_str("L M' x2 (R' S2 z)")
    move_meta = MoveMeta.from_puzzle(puzzle=Puzzle._3x3x3)

    result = invert(seq, move_meta)
    assert result == MoveSequence.from_str("x2 M L' (z' S2 R)")
