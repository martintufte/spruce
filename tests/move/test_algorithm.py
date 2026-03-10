import pytest

from rubiks_cube.move.algorithm import MoveAlgorithm
from rubiks_cube.move.sequence import MoveSequence


class TestMoveAlgorithmBasics:
    """Test basic MoveAlgorithm construction and operations."""

    def test_initialization(self) -> None:
        """Test basic initialization."""
        alg = MoveAlgorithm("sune", MoveSequence.from_str("R U R' U R U2 R'"))
        assert alg.name == "sune"
        assert alg.sequence == MoveSequence.from_str("R U R' U R U2 R'")

    def test_initialization_with_cube_range(self) -> None:
        """Test initialization with cube range."""
        alg = MoveAlgorithm("sune", MoveSequence.from_str("R U R' U R U2 R'"))
        assert alg.name == "sune"
        assert alg.sequence == MoveSequence.from_str("R U R' U R U2 R'")

    def test_initialization_with_empty_sequence(self) -> None:
        """Test initialization with empty sequence."""
        alg = MoveAlgorithm("empty", MoveSequence())
        assert alg.name == "empty"
        assert len(alg.sequence) == 0

    def test_invalid_name_with_space(self) -> None:
        """Test that name cannot contain spaces."""
        with pytest.raises(ValueError, match=r"Algorithm name got unsupported characters"):
            MoveAlgorithm("su ne", MoveSequence.from_str("R U"))

    def test_invalid_name_non_ascii(self) -> None:
        """Test that name must be ASCII."""
        with pytest.raises(ValueError, match=r"Algorithm name got unsupported characters"):
            MoveAlgorithm("sünë", MoveSequence.from_str("R U"))

    def test_string_representation(self) -> None:
        """Test string representation."""
        alg = MoveAlgorithm("sune", MoveSequence.from_str("R U R' U R U2 R'"))
        assert str(alg) == ":sune:"

    def test_repr(self) -> None:
        """Test repr representation."""
        alg = MoveAlgorithm("sune", MoveSequence.from_str("R U R'"))
        assert repr(alg) == "MoveAlgorithm('sune', R U R')"

    def test_len(self) -> None:
        """Test length of algorithm."""
        alg = MoveAlgorithm("test", MoveSequence.from_str("R U R' U'"))
        assert len(alg) == 4

    def test_len_empty(self) -> None:
        """Test length of empty algorithm."""
        alg = MoveAlgorithm("empty", MoveSequence())
        assert len(alg) == 0


class TestMoveAlgorithmEdgeCases:
    """Test edge cases and special scenarios."""

    def test_algorithm_with_wide_moves(self) -> None:
        """Test algorithm with wide moves."""
        alg = MoveAlgorithm("wide", MoveSequence.from_str("Rw U Rw'"))
        assert alg.sequence == MoveSequence.from_str("Rw U Rw'")

    def test_algorithm_with_slice_moves(self) -> None:
        """Test algorithm with slice moves."""
        alg = MoveAlgorithm("slice", MoveSequence.from_str("M E S"))
        assert alg.sequence == MoveSequence.from_str("M E S")

    def test_algorithm_with_rotations(self) -> None:
        """Test algorithm with rotations."""
        alg = MoveAlgorithm("rotation", MoveSequence.from_str("x R U R' x'"))
        assert alg.sequence == MoveSequence.from_str("x R U R' x'")

    def test_algorithm_with_niss(self) -> None:
        """Test algorithm with NISS notation."""
        alg = MoveAlgorithm("niss", MoveSequence.from_str("R (U) R'"))
        assert alg.sequence == MoveSequence.from_str("R (U) R'")

    def test_long_algorithm_name(self) -> None:
        """Test algorithm with long name."""
        long_name = "a" * 100
        alg = MoveAlgorithm(long_name, MoveSequence.from_str("R U"))
        assert alg.name == long_name

    def test_complex_sequence(self) -> None:
        """Test algorithm with complex sequence."""
        seq = MoveSequence.from_str("R U R' U' R' F R2 U' R' U' R U R' F'")
        alg = MoveAlgorithm("tperm", seq)
        assert len(alg) == 14
        assert alg.sequence == seq
