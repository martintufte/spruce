import pytest

from rubiks_cube.configuration.enumeration import Metric
from rubiks_cube.move.meta import MoveMeta
from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.move.sequence import cleanup
from rubiks_cube.move.sequence import decompose
from rubiks_cube.move.sequence import measure
from rubiks_cube.move.sequence import niss
from rubiks_cube.move.sequence import replace_slice_moves
from rubiks_cube.move.sequence import replace_wide_moves
from rubiks_cube.move.sequence import shift_rotations_to_end
from rubiks_cube.move.sequence import try_cancel_moves
from rubiks_cube.move.sequence import unniss


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
        assert seq.moves == ["R", "U", "R'", "U'"]

    def test_list_initialization(self) -> None:
        """Test initialization from list."""
        seq = MoveSequence(["R", "U", "R'", "U'"])
        assert len(seq) == 4
        assert seq.moves == ["R", "U", "R'", "U'"]

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

    def test_indexing(self) -> None:
        """Test indexing and slicing."""
        seq = MoveSequence.from_str("R U R' U'")
        assert seq[0] == "R"
        assert seq[-1] == "U'"
        assert list(seq[1:3]) == ["U", "R'"]

    def test_contains(self) -> None:
        """Test membership checking."""
        seq = MoveSequence.from_str("R U R' U'")
        assert "R" in seq
        assert "F" not in seq

    def test_iteration(self) -> None:
        """Test iteration over moves."""
        seq = MoveSequence.from_str("R U R' U'")
        moves = list(seq)
        assert moves == ["R", "U", "R'", "U'"]

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
        assert seq.moves is not seq_copy.moves


@pytest.mark.parametrize(
    ("move", "expected"),
    [
        ("", ""),
        ("x2 y2", "z2"),
        ("y2 z2", "x2"),
        ("z2 x2", "y2"),
        ("x y2 z' x' y2 x2 z' y' x y2 x' z2 y' x2 z' y2", "y"),
    ],
)
def test_shift_rotations_to_end(move: str, expected: str) -> None:
    """Test that rotations are combined and moved to end."""
    seq = MoveSequence.from_str(move)
    shift_rotations_to_end(seq)
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
def test_try_cancel_moves(move: str, expected: str) -> None:
    """Test that permutation-aware cancellation works for non-rotations."""
    seq = MoveSequence.from_str(move)
    move_meta = MoveMeta.from_cube_size(3)
    try_cancel_moves(seq, move_meta)
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
    replace_wide_moves(seq, cube_size=3)
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
    replace_wide_moves(seq, cube_size=9)
    assert seq == MoveSequence.from_str(expected)


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
    replace_wide_moves(seq, cube_size=3)
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
    replace_slice_moves(seq)
    assert seq == MoveSequence.from_str(expected)


def test_decompose() -> None:
    """Test decomposing sequence into normal and inverse moves."""
    seq = MoveSequence.from_str("R U (R' U') R2")
    normal, inverse = decompose(seq)
    assert normal == MoveSequence.from_str("R U R2")
    assert inverse == MoveSequence.from_str("R' U'")


def test_unniss() -> None:
    """Test unnissing a sequence."""
    seq = MoveSequence.from_str("R U (R' U')")
    result = unniss(seq)
    assert result == MoveSequence.from_str("R U U R")


def test_measure() -> None:
    """Test measuring sequence length."""
    seq = MoveSequence.from_str("R U R' U'")
    assert measure(seq, Metric.HTM) == 4


def test_cleanup() -> None:
    """Test sequence cleanup combines operations."""
    seq = MoveSequence.from_str("(R') L M' (S2) x2 (z)")
    move_meta = MoveMeta.from_cube_size(3)
    cleaned_seq = cleanup(seq, move_meta)
    assert cleaned_seq == MoveSequence.from_str("L2 R' x' (R' F2 B2 z')")


def test_invert() -> None:
    """Test sequence inversion reverses and inverts each move."""
    seq = MoveSequence.from_str("L M' x2 (R' S2 z)")
    assert ~seq == MoveSequence.from_str("(z' S2 R) x2 M L'")


@pytest.mark.parametrize(
    ("move", "expected"),
    [
        ("R", "(R)"),
        ("(R)", "R"),
        ("R U", "(R U)"),
        ("(R U)", "R U"),
    ],
)
def test_niss(move: str, expected: str) -> None:
    """Test NISS toggle wraps/unwraps moves in parentheses."""
    seq = MoveSequence.from_str(move)
    niss(seq)
    assert seq == MoveSequence.from_str(expected)
