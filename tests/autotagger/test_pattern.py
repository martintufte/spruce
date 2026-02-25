from __future__ import annotations

import math

from rubiks_cube.autotagger.pattern import Pattern
from rubiks_cube.autotagger.pattern import get_patterns
from rubiks_cube.configuration.enumeration import Goal
from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.representation import get_rubiks_cube_permutation
from rubiks_cube.representation.pattern import get_empty_pattern
from rubiks_cube.representation.pattern import get_identity_pattern
from rubiks_cube.representation.permutation import get_identity_permutation


class TestPatternBasics:
    """Test basic Pattern functionality."""

    def test_pattern_initialization(self) -> None:
        """Test Pattern initialization."""
        pattern = get_identity_pattern(cube_size=3)
        pattern = Pattern(patterns=[pattern], names=["test"])
        assert len(pattern) == 1
        assert pattern.names == ["test"]

    def test_pattern_with_multiple_patterns(self) -> None:
        """Test Pattern with multiple patterns."""
        pattern1 = get_identity_pattern(cube_size=3)
        pattern2 = get_empty_pattern(cube_size=3)
        pattern = Pattern(patterns=[pattern1, pattern2], names=["solved", "empty"])
        assert len(pattern) == 2
        assert pattern.names == ["solved", "empty"]

    def test_pattern_repr(self) -> None:
        """Test Pattern string representation."""
        pattern = get_identity_pattern(cube_size=3)
        pattern = Pattern(patterns=[pattern], names=["test"])
        repr_str = repr(pattern)
        assert "Pattern" in repr_str
        assert "patterns" in repr_str


class TestPatternOperations:
    """Test Pattern operations (OR, AND, contains)."""

    def test_pattern_or_operation(self) -> None:
        """Test OR operation between Patternes."""
        pattern1 = get_identity_pattern(cube_size=3)
        pattern2 = get_empty_pattern(cube_size=3)
        pattern1 = Pattern(patterns=[pattern1], names=["test1"])
        pattern2 = Pattern(patterns=[pattern2], names=["test2"])

        result = pattern1 | pattern2
        assert len(result) == 2
        assert result.names == ["test1", "test2"]

    def test_pattern_and_operation(self) -> None:
        """Test AND operation between Patternes."""
        pattern1 = get_identity_pattern(cube_size=3)
        pattern2 = get_identity_pattern(cube_size=3)
        pattern1 = Pattern(patterns=[pattern1], names=["test1"])
        pattern2 = Pattern(patterns=[pattern2], names=["test2"])

        result = pattern1 & pattern2
        assert len(result) >= 1  # At least one merged pattern
        assert any("&" in name for name in result.names)

    def test_pattern_contains_self(self) -> None:
        """Test that pattern contains itself."""
        pattern = get_identity_pattern(cube_size=3)
        pattern1 = Pattern(patterns=[pattern], names=["test"])
        pattern2 = Pattern(patterns=[pattern], names=["test"])
        assert pattern1 in pattern2

    def test_pattern_contains_invalid_type(self) -> None:
        """Test that contains returns False for invalid types."""
        pattern = get_identity_pattern(cube_size=3)
        pattern = Pattern(patterns=[pattern], names=["test"])
        # Contains checks for Pattern type, so these will return False
        assert "invalid" not in pattern
        assert 42 not in pattern


class TestPatternMatch:
    """Test Pattern pattern matching."""

    def test_match_solved_cube(self) -> None:
        """Test matching solved cube."""
        pattern = get_identity_pattern(cube_size=3)
        pattern = Pattern(patterns=[pattern], names=["solved"])
        permutation = get_identity_permutation()
        assert pattern.match(permutation)

    def test_no_match_scrambled_cube(self) -> None:
        """Test that solved pattern doesn't match scrambled cube."""
        pattern = get_identity_pattern(cube_size=3)
        pattern = Pattern(patterns=[pattern], names=["solved"])
        permutation = get_rubiks_cube_permutation(MoveSequence.from_str("U"))
        assert not pattern.match(permutation)

    def test_match_with_multiple_patterns(self) -> None:
        """Test matching with multiple patterns."""
        pattern1 = get_identity_pattern(cube_size=3)
        pattern2 = get_empty_pattern(cube_size=3)
        pattern = Pattern(patterns=[pattern1, pattern2], names=["p1", "p2"])

        # Solved cube should match first pattern
        permutation = get_identity_permutation()
        assert pattern.match(permutation)


class TestPatternProperties:
    """Test Pattern properties (entropy, combinations)."""

    def test_combinations_and_entropy(self) -> None:
        """Test combinations and entropy properties together."""
        pattern = get_identity_pattern(cube_size=3)
        pattern = Pattern(patterns=[pattern], names=["solved"])

        # Test combinations
        combinations = pattern.combinations
        assert isinstance(combinations, int)
        assert combinations > 0

        # Test entropy
        entropy = pattern.entropy
        assert isinstance(entropy, float)
        assert entropy >= 0

        # Test relationship: entropy should be log2(combinations)
        expected_entropy = math.log2(combinations)
        assert abs(entropy - expected_entropy) < 1e-10


class TestPatternContains:
    """Test Pattern containment relationships."""

    def test_dr_contains_eo(self) -> None:
        """Test that DR contains EO."""
        cube_size = 3
        patterns = get_patterns(cube_size=cube_size)

        assert patterns[Goal.eo_fb] in patterns[Goal.dr_ud]
        assert patterns[Goal.dr_ud] not in patterns[Goal.eo_fb]

    def test_solved_contains_all(self) -> None:
        """Test that solved contains all other patterns."""
        cube_size = 3
        patterns = get_patterns(cube_size=cube_size)

        for pattern in patterns:
            assert patterns[pattern] in patterns[Goal.solved]
            if pattern is not Goal.solved:
                assert patterns[Goal.solved] not in patterns[pattern]

    def test_cross_in_f2l(self) -> None:
        """Test that cross is contained in F2L."""
        cube_size = 3
        patterns = get_patterns(cube_size=cube_size)

        if Goal.cross in patterns and Goal.f2l in patterns:
            assert patterns[Goal.cross] in patterns[Goal.f2l]


class TestGetPatternes:
    """Test get_patterns function."""

    def test_get_patterns_returns_valid_patterns(self) -> None:
        """Test that get_patterns returns required patterns."""
        cube_size = 3
        patterns = get_patterns(cube_size=cube_size)

        # Basic validation
        assert isinstance(patterns, dict)
        assert len(patterns) > 0

        # Required patterns exist
        required_patterns = [Goal.solved, Goal.cross, Goal.f2l]
        for pattern in required_patterns:
            assert pattern in patterns
            assert isinstance(patterns[pattern], Pattern)

    def test_get_patterns_caching(self) -> None:
        """Test that get_patterns uses caching."""
        cube_size = 3
        patterns1 = get_patterns(cube_size=cube_size)
        patterns2 = get_patterns(cube_size=cube_size)

        # Should be the same object due to LRU caching
        assert patterns1 is patterns2


class TestPatternEdgeCases:
    """Test edge cases for Pattern."""

    def test_empty_pattern(self) -> None:
        """Test creating empty pattern."""
        pattern = Pattern(patterns=[], names=[])
        assert len(pattern) == 0

    def test_pattern_match_with_empty_patterns(self) -> None:
        """Test matching with empty patterns list."""
        pattern = Pattern(patterns=[], names=[])
        permutation = get_rubiks_cube_permutation(MoveSequence())
        # Empty pattern should not match anything
        assert not pattern.match(permutation)

    def test_pattern_entropy_with_single_pattern(self) -> None:
        """Test entropy calculation with single pattern."""
        pattern = get_identity_pattern(cube_size=3)
        pattern = Pattern(patterns=[pattern], names=["test"])
        # Entropy should be finite and non-negative
        assert 0 <= pattern.entropy < float("inf")
