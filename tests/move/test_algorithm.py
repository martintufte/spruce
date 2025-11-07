import pytest

from rubiks_cube.move.algorithm import MoveAlgorithm
from rubiks_cube.move.sequence import MoveSequence


class TestMoveAlgorithmBasics:
    """Test basic MoveAlgorithm construction and operations."""

    def test_initialization(self) -> None:
        """Test basic initialization."""
        alg = MoveAlgorithm("sune", MoveSequence("R U R' U R U2 R'"))
        assert alg.name == "sune"
        assert alg.sequence == MoveSequence("R U R' U R U2 R'")
        assert alg.cube_range == (None, None)

    def test_initialization_with_cube_range(self) -> None:
        """Test initialization with cube range."""
        alg = MoveAlgorithm("sune", MoveSequence("R U R' U R U2 R'"), cube_range=(3, None))
        assert alg.name == "sune"
        assert alg.sequence == MoveSequence("R U R' U R U2 R'")
        assert alg.cube_range == (3, None)

    def test_initialization_with_bounded_range(self) -> None:
        """Test initialization with bounded cube range."""
        alg = MoveAlgorithm("test", MoveSequence("R U"), cube_range=(2, 5))
        assert alg.cube_range == (2, 5)

    def test_initialization_with_empty_sequence(self) -> None:
        """Test initialization with empty sequence."""
        alg = MoveAlgorithm("empty", MoveSequence())
        assert alg.name == "empty"
        assert len(alg.sequence) == 0

    def test_invalid_name_too_short(self) -> None:
        """Test that name must be at least 2 characters."""
        with pytest.raises(AssertionError, match="Invalid algorithm name!"):
            MoveAlgorithm("x", MoveSequence("R U"))

    def test_invalid_name_with_space(self) -> None:
        """Test that name cannot contain spaces."""
        with pytest.raises(AssertionError, match="Invalid algorithm name!"):
            MoveAlgorithm("su ne", MoveSequence("R U"))

    def test_invalid_name_non_ascii(self) -> None:
        """Test that name must be ASCII."""
        with pytest.raises(AssertionError, match="Invalid algorithm name!"):
            MoveAlgorithm("sünë", MoveSequence("R U"))

    def test_invalid_cube_range_too_small(self) -> None:
        """Test that cube range minimum must be at least 1."""
        with pytest.raises(AssertionError, match="Cube size too small!"):
            MoveAlgorithm("test", MoveSequence("R U"), cube_range=(0, None))

    def test_string_representation(self) -> None:
        """Test string representation."""
        alg = MoveAlgorithm("sune", MoveSequence("R U R' U R U2 R'"))
        assert str(alg) == "MoveAlgorithm('sune': R U R' U R U2 R')"

    def test_string_representation_empty(self) -> None:
        """Test string representation with empty sequence."""
        alg = MoveAlgorithm("empty", MoveSequence())
        assert str(alg) == "MoveAlgorithm('empty': )"

    def test_repr(self) -> None:
        """Test repr representation."""
        alg = MoveAlgorithm("sune", MoveSequence("R U R'"))
        assert repr(alg) == "MoveAlgorithm('sune', R U R')"

    def test_len(self) -> None:
        """Test length of algorithm."""
        alg = MoveAlgorithm("test", MoveSequence("R U R' U'"))
        assert len(alg) == 4

    def test_len_empty(self) -> None:
        """Test length of empty algorithm."""
        alg = MoveAlgorithm("empty", MoveSequence())
        assert len(alg) == 0


class TestMoveAlgorithmEquality:
    """Test equality and comparison operations."""

    def test_equality_same_sequence(self) -> None:
        """Test equality for algorithms with same sequence."""
        alg1 = MoveAlgorithm("test1", MoveSequence("R U R' U'"))
        alg2 = MoveAlgorithm("test2", MoveSequence("R U R' U'"))
        assert alg1 == alg2

    def test_equality_equivalent_sequences(self) -> None:
        """Test equality for algorithms with equivalent sequences."""
        alg1 = MoveAlgorithm("test1", MoveSequence("R R"))
        alg2 = MoveAlgorithm("test2", MoveSequence("R2"))
        # They produce the same permutation, so should be equal
        assert alg1 == alg2

    def test_inequality_different_sequences(self) -> None:
        """Test inequality for different sequences."""
        alg1 = MoveAlgorithm("test1", MoveSequence("R U"))
        alg2 = MoveAlgorithm("test2", MoveSequence("U R"))
        assert alg1 != alg2

    def test_equality_empty_algorithms(self) -> None:
        """Test equality for empty algorithms."""
        alg1 = MoveAlgorithm("empty1", MoveSequence())
        alg2 = MoveAlgorithm("empty2", MoveSequence())
        assert alg1 == alg2

    def test_inequality_with_non_algorithm(self) -> None:
        """Test inequality with non-algorithm object."""
        alg = MoveAlgorithm("test", MoveSequence("R U"))
        assert alg != "R U"
        assert alg != MoveSequence("R U")
        assert alg != 42


class TestMoveAlgorithmComparison:
    """Test comparison operators."""

    def test_less_than(self) -> None:
        """Test less than comparison based on length."""
        alg1 = MoveAlgorithm("short", MoveSequence("R U"))
        alg2 = MoveAlgorithm("long", MoveSequence("R U R' U'"))
        assert alg1 < alg2

    def test_less_than_equal_lengths(self) -> None:
        """Test less than with equal lengths."""
        alg1 = MoveAlgorithm("test1", MoveSequence("R U"))
        alg2 = MoveAlgorithm("test2", MoveSequence("F D"))
        assert not (alg1 < alg2)

    def test_less_than_or_equal(self) -> None:
        """Test less than or equal comparison."""
        alg1 = MoveAlgorithm("short", MoveSequence("R U"))
        alg2 = MoveAlgorithm("long", MoveSequence("R U R' U'"))
        alg3 = MoveAlgorithm("same", MoveSequence("F D"))
        assert alg1 <= alg2
        assert alg1 <= alg3

    def test_greater_than(self) -> None:
        """Test greater than comparison."""
        alg1 = MoveAlgorithm("long", MoveSequence("R U R' U'"))
        alg2 = MoveAlgorithm("short", MoveSequence("R U"))
        assert alg1 > alg2

    def test_greater_than_or_equal(self) -> None:
        """Test greater than or equal comparison."""
        alg1 = MoveAlgorithm("long", MoveSequence("R U R' U'"))
        alg2 = MoveAlgorithm("short", MoveSequence("R U"))
        alg3 = MoveAlgorithm("same", MoveSequence("F D"))
        assert alg1 >= alg2
        assert alg2 >= alg3

    def test_comparison_with_non_algorithm(self) -> None:
        """Test that comparison with non-algorithm returns False."""
        alg = MoveAlgorithm("test", MoveSequence("R U"))
        assert not (alg < "R U")
        assert not (alg <= "R U")
        assert not (alg > "R U")
        assert not (alg >= "R U")


class TestMoveAlgorithmEdgeCases:
    """Test edge cases and special scenarios."""

    def test_algorithm_with_wide_moves(self) -> None:
        """Test algorithm with wide moves."""
        alg = MoveAlgorithm("wide", MoveSequence("Rw U Rw'"))
        assert alg.sequence == MoveSequence("Rw U Rw'")

    def test_algorithm_with_slice_moves(self) -> None:
        """Test algorithm with slice moves."""
        alg = MoveAlgorithm("slice", MoveSequence("M E S"))
        assert alg.sequence == MoveSequence("M E S")

    def test_algorithm_with_rotations(self) -> None:
        """Test algorithm with rotations."""
        alg = MoveAlgorithm("rotation", MoveSequence("x R U R' x'"))
        assert alg.sequence == MoveSequence("x R U R' x'")

    def test_algorithm_with_niss(self) -> None:
        """Test algorithm with NISS notation."""
        alg = MoveAlgorithm("niss", MoveSequence("R (U) R'"))
        assert alg.sequence == MoveSequence("R (U) R'")

    def test_long_algorithm_name(self) -> None:
        """Test algorithm with long name."""
        long_name = "a" * 100
        alg = MoveAlgorithm(long_name, MoveSequence("R U"))
        assert alg.name == long_name

    def test_cube_range_with_none_lower(self) -> None:
        """Test cube range with None as lower bound."""
        alg = MoveAlgorithm("test", MoveSequence("R U"), cube_range=(None, 5))
        assert alg.cube_range == (None, 5)

    def test_cube_range_single_size(self) -> None:
        """Test cube range with same min and max."""
        alg = MoveAlgorithm("test", MoveSequence("R U"), cube_range=(3, 3))
        assert alg.cube_range == (3, 3)

    def test_complex_sequence(self) -> None:
        """Test algorithm with complex sequence."""
        seq = MoveSequence("R U R' U' R' F R2 U' R' U' R U R' F'")
        alg = MoveAlgorithm("tperm", seq)
        assert len(alg) == 14
        assert alg.sequence == seq
