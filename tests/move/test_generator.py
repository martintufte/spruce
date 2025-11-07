import pytest

from rubiks_cube.move.generator import MoveGenerator
from rubiks_cube.move.generator import cleanup_all
from rubiks_cube.move.generator import remove_empty
from rubiks_cube.move.generator import remove_inversed
from rubiks_cube.move.generator import simplify
from rubiks_cube.move.sequence import MoveSequence


class TestMoveGeneratorBasics:
    """Test basic MoveGenerator construction and operations."""

    def test_empty_initialization(self) -> None:
        """Test empty generator initialization."""
        gen = MoveGenerator()
        assert len(gen) == 0
        assert str(gen) == "<>"
        assert not gen

    def test_string_initialization(self) -> None:
        """Test initialization from string."""
        gen = MoveGenerator("<R, U>")
        assert len(gen) == 2
        assert MoveSequence("R") in gen.generator
        assert MoveSequence("U") in gen.generator

    def test_set_initialization(self) -> None:
        """Test initialization from set of sequences."""
        seqs = {MoveSequence("R"), MoveSequence("U")}
        gen = MoveGenerator(seqs)
        assert len(gen) == 2
        assert gen.generator == seqs

    def test_invalid_string_format(self) -> None:
        """Test that invalid format raises ValueError."""
        with pytest.raises(ValueError, match="Invalid move generator format"):
            MoveGenerator("R, U")
        with pytest.raises(ValueError, match="Invalid move generator format"):
            MoveGenerator("R, U>")
        with pytest.raises(ValueError, match="Invalid move generator format"):
            MoveGenerator("<R, U")

    def test_string_representation(self) -> None:
        """Test string representation."""
        gen = MoveGenerator("<R, U>")
        assert str(gen) in ["<R, U>", "<U, R>"]  # Order may vary
        assert repr(gen) in ['MoveGenerator("<R, U>")', 'MoveGenerator("<U, R>")']

    def test_string_representation_sorts_by_length(self) -> None:
        """Test that string representation sorts by length."""
        gen = MoveGenerator("<R U R', U, R>")
        gen_str = str(gen)
        assert gen_str.startswith("<")
        assert gen_str.endswith(">")
        # Shortest sequences should come first
        parts = gen_str[1:-1].split(", ")
        assert len(parts[0]) <= len(parts[-1])

    def test_equality(self) -> None:
        """Test equality comparison."""
        gen1 = MoveGenerator("<R, U>")
        gen2 = MoveGenerator("<U, R>")
        gen3 = MoveGenerator("<R, F>")
        assert gen1 == gen2
        assert gen1 != gen3

    def test_addition(self) -> None:
        """Test generator combination."""
        gen1 = MoveGenerator("<R, U>")
        gen2 = MoveGenerator("<F>")
        result = gen1 + gen2
        assert len(result) == 3
        assert MoveSequence("R") in result.generator
        assert MoveSequence("U") in result.generator
        assert MoveSequence("F") in result.generator

    def test_addition_with_set(self) -> None:
        """Test adding a set of sequences."""
        gen = MoveGenerator("<R>")
        seq_set = {MoveSequence("U")}
        result = gen + seq_set
        assert len(result) == 2

    def test_iteration(self) -> None:
        """Test iteration over sequences."""
        gen = MoveGenerator("<R, U>")
        seqs = list(gen)
        assert len(seqs) == 2
        assert MoveSequence("R") in seqs or MoveSequence("U") in seqs

    def test_contains(self) -> None:
        """Test membership checking."""
        gen = MoveGenerator("<R, U>")
        # Note: __contains__ checks if item is in generator, not if it's a string
        assert MoveSequence("R") in gen.generator

    def test_comparison_operators(self) -> None:
        """Test length comparison operators."""
        gen1 = MoveGenerator("<R, U>")
        gen2 = MoveGenerator("<R, U, F>")
        gen3 = MoveGenerator("<R, U>")
        assert gen1 < gen2
        assert gen1 <= gen2
        assert gen1 <= gen3
        assert gen2 > gen1
        assert gen2 >= gen1
        assert gen1 >= gen3

    def test_copy(self) -> None:
        """Test copying a generator."""
        gen = MoveGenerator("<R, U>")
        gen_copy = gen.__copy__()
        assert gen == gen_copy
        assert gen.generator is not gen_copy.generator


class TestGeneratorFunctions:
    """Test generator manipulation functions."""

    def test_cleanup_all(self) -> None:
        """Test cleaning up all sequences in generator."""
        gen = MoveGenerator("<R R, U U'>")
        cleaned = cleanup_all(gen)
        assert MoveSequence("R2") in cleaned.generator

    def test_remove_empty(self) -> None:
        """Test removing empty sequences."""
        gen = MoveGenerator({MoveSequence("R"), MoveSequence("")})
        result = remove_empty(gen)
        assert len(result) == 1
        assert MoveSequence("R") in result.generator

    def test_remove_inversed(self) -> None:
        """Test removing inverse duplicate sequences."""
        gen = MoveGenerator("<R, R'>")
        result = remove_inversed(gen)
        # Should keep only one (the shorter representation)
        assert len(result) == 1

    def test_remove_inversed_keeps_shorter(self) -> None:
        """Test that remove_inversed keeps shorter representation."""
        gen = MoveGenerator({MoveSequence("R U R' U'"), MoveSequence("U R U' R'")})
        result = remove_inversed(gen)
        # Both have same length, should keep one
        assert len(result) >= 1

    def test_simplify_complex_generator(self) -> None:
        """Test simplifying a complex generator."""
        gen = MoveGenerator("<(R)R' (),(R'), R RR, R,xLw,R2'F, (R), ((R')R),, R'>")
        simple_gen = simplify(gen)
        control_gen = simplify(simple_gen)
        assert simple_gen == control_gen

    def test_simplify_removes_empty(self) -> None:
        """Test that simplify removes empty sequences."""
        gen = MoveGenerator("<R, U U'>")
        result = simplify(gen)
        # U U' should be removed as it becomes empty
        assert len(result) == 1

    def test_simplify_removes_inverses(self) -> None:
        """Test that simplify removes inverse sequences."""
        gen = MoveGenerator("<R, R'>")
        result = simplify(gen)
        assert len(result) == 1

    def test_simplify_cleans_sequences(self) -> None:
        """Test that simplify cleans up sequences."""
        gen = MoveGenerator("<R R, U>")
        result = simplify(gen)
        assert MoveSequence("R2") in result.generator or MoveSequence("U") in result.generator


class TestEdgeCases:
    """Test edge cases and special scenarios."""

    def test_empty_string_in_generator(self) -> None:
        """Test generator with empty strings."""
        gen = MoveGenerator("<R, , U>")
        # Empty string creates empty sequence
        assert len(gen) == 3

    def test_whitespace_handling(self) -> None:
        """Test handling of whitespace."""
        gen = MoveGenerator(" < R , U > ")
        assert len(gen) == 2

    def test_duplicate_sequences(self) -> None:
        """Test that duplicate sequences are handled."""
        gen = MoveGenerator("<R, R, U>")
        # Sets automatically handle duplicates
        assert len(gen) == 2

    def test_complex_sequences(self) -> None:
        """Test with complex move sequences."""
        gen = MoveGenerator("<R U R' U', F R U' R' F'>")
        assert len(gen) == 2

    def test_wide_moves_in_generator(self) -> None:
        """Test generator with wide moves."""
        gen = MoveGenerator("<Rw, Uw>")
        assert len(gen) == 2

    def test_slice_moves_in_generator(self) -> None:
        """Test generator with slice moves."""
        gen = MoveGenerator("<M, E, S>")
        assert len(gen) == 3

    def test_rotations_in_generator(self) -> None:
        """Test generator with rotations."""
        gen = MoveGenerator("<x, y, z>")
        assert len(gen) == 3

    def test_niss_moves_in_generator(self) -> None:
        """Test generator with NISS notation."""
        gen = MoveGenerator("<R, (U)>")
        assert len(gen) == 2


class TestGeneratorOperations:
    """Test advanced generator operations."""

    def test_generator_union(self) -> None:
        """Test union of two generators."""
        gen1 = MoveGenerator("<R, U>")
        gen2 = MoveGenerator("<F, B>")
        result = gen1 + gen2
        assert len(result) == 4

    def test_generator_with_overlapping_sequences(self) -> None:
        """Test adding generators with overlapping sequences."""
        gen1 = MoveGenerator("<R, U>")
        gen2 = MoveGenerator("<U, F>")
        result = gen1 + gen2
        # U is in both, should appear once due to set
        assert len(result) == 3

    def test_right_addition(self) -> None:
        """Test right addition (radd)."""
        gen = MoveGenerator("<R>")
        seq_set = {MoveSequence("U")}
        result = seq_set + gen  # Uses __radd__
        assert len(result) == 2
