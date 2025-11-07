from __future__ import annotations

import math

from rubiks_cube.autotagger.cubex import Cubex
from rubiks_cube.autotagger.cubex import get_cubexes
from rubiks_cube.configuration.enumeration import Goal
from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.representation import get_rubiks_cube_state
from rubiks_cube.representation.pattern import get_empty_pattern
from rubiks_cube.representation.pattern import get_solved_pattern


class TestCubexBasics:
    """Test basic Cubex functionality."""

    def test_cubex_initialization(self) -> None:
        """Test Cubex initialization."""
        pattern = get_solved_pattern(cube_size=3)
        cubex = Cubex(patterns=[pattern], names=["test"])
        assert len(cubex) == 1
        assert cubex.names == ["test"]

    def test_cubex_with_multiple_patterns(self) -> None:
        """Test Cubex with multiple patterns."""
        pattern1 = get_solved_pattern(cube_size=3)
        pattern2 = get_empty_pattern(cube_size=3)
        cubex = Cubex(patterns=[pattern1, pattern2], names=["solved", "empty"])
        assert len(cubex) == 2
        assert cubex.names == ["solved", "empty"]

    def test_cubex_repr(self) -> None:
        """Test Cubex string representation."""
        pattern = get_solved_pattern(cube_size=3)
        cubex = Cubex(patterns=[pattern], names=["test"])
        repr_str = repr(cubex)
        assert "Cubex" in repr_str
        assert "patterns" in repr_str


class TestCubexOperations:
    """Test Cubex operations (OR, AND, contains)."""

    def test_cubex_or_operation(self) -> None:
        """Test OR operation between Cubexes."""
        pattern1 = get_solved_pattern(cube_size=3)
        pattern2 = get_empty_pattern(cube_size=3)
        cubex1 = Cubex(patterns=[pattern1], names=["test1"])
        cubex2 = Cubex(patterns=[pattern2], names=["test2"])

        result = cubex1 | cubex2
        assert len(result) == 2
        assert result.names == ["test1", "test2"]

    def test_cubex_and_operation(self) -> None:
        """Test AND operation between Cubexes."""
        pattern1 = get_solved_pattern(cube_size=3)
        pattern2 = get_solved_pattern(cube_size=3)
        cubex1 = Cubex(patterns=[pattern1], names=["test1"])
        cubex2 = Cubex(patterns=[pattern2], names=["test2"])

        result = cubex1 & cubex2
        assert len(result) >= 1  # At least one merged pattern
        assert any("&" in name for name in result.names)

    def test_cubex_contains_self(self) -> None:
        """Test that cubex contains itself."""
        pattern = get_solved_pattern(cube_size=3)
        cubex1 = Cubex(patterns=[pattern], names=["test"])
        cubex2 = Cubex(patterns=[pattern], names=["test"])
        assert cubex1 in cubex2

    def test_cubex_contains_invalid_type(self) -> None:
        """Test that contains returns False for invalid types."""
        pattern = get_solved_pattern(cube_size=3)
        cubex = Cubex(patterns=[pattern], names=["test"])
        # Contains checks for Cubex type, so these will return False
        assert "invalid" not in cubex
        assert 42 not in cubex


class TestCubexMatch:
    """Test Cubex pattern matching."""

    def test_match_solved_state(self) -> None:
        """Test matching solved state."""
        pattern = get_solved_pattern(cube_size=3)
        cubex = Cubex(patterns=[pattern], names=["solved"])
        permutation = get_rubiks_cube_state(MoveSequence())
        assert cubex.match(permutation)

    def test_no_match_scrambled_state(self) -> None:
        """Test that solved pattern doesn't match scrambled state."""
        pattern = get_solved_pattern(cube_size=3)
        cubex = Cubex(patterns=[pattern], names=["solved"])
        permutation = get_rubiks_cube_state(MoveSequence("R U R' U'"))
        assert not cubex.match(permutation)

    def test_match_with_multiple_patterns(self) -> None:
        """Test matching with multiple patterns."""
        pattern1 = get_solved_pattern(cube_size=3)
        pattern2 = get_empty_pattern(cube_size=3)
        cubex = Cubex(patterns=[pattern1, pattern2], names=["p1", "p2"])

        # Solved state should match first pattern
        permutation = get_rubiks_cube_state(MoveSequence())
        assert cubex.match(permutation)


class TestCubexProperties:
    """Test Cubex properties (entropy, combinations)."""

    def test_combinations_and_entropy(self) -> None:
        """Test combinations and entropy properties together."""
        pattern = get_solved_pattern(cube_size=3)
        cubex = Cubex(patterns=[pattern], names=["solved"])

        # Test combinations
        combinations = cubex.combinations
        assert isinstance(combinations, int)
        assert combinations > 0

        # Test entropy
        entropy = cubex.entropy
        assert isinstance(entropy, float)
        assert entropy >= 0

        # Test relationship: entropy should be log2(combinations)
        expected_entropy = math.log2(combinations)
        assert abs(entropy - expected_entropy) < 1e-10


class TestCubexContains:
    """Test Cubex containment relationships."""

    def test_dr_contains_eo(self) -> None:
        """Test that DR contains EO."""
        cube_size = 3
        cubexes = get_cubexes(cube_size=cube_size)

        assert cubexes[Goal.eo_fb] in cubexes[Goal.dr_ud]
        assert cubexes[Goal.dr_ud] not in cubexes[Goal.eo_fb]

    def test_solved_contains_all(self) -> None:
        """Test that solved contains all other patterns."""
        cube_size = 3
        cubexes = get_cubexes(cube_size=cube_size)

        for pattern in cubexes:
            assert cubexes[pattern] in cubexes[Goal.solved]
            if pattern is not Goal.solved:
                assert cubexes[Goal.solved] not in cubexes[pattern]

    def test_cross_in_f2l(self) -> None:
        """Test that cross is contained in F2L."""
        cube_size = 3
        cubexes = get_cubexes(cube_size=cube_size)

        if Goal.cross in cubexes and Goal.f2l in cubexes:
            assert cubexes[Goal.cross] in cubexes[Goal.f2l]


class TestGetCubexes:
    """Test get_cubexes function."""

    def test_get_cubexes_returns_valid_patterns(self) -> None:
        """Test that get_cubexes returns required patterns."""
        cube_size = 3
        cubexes = get_cubexes(cube_size=cube_size)

        # Basic validation
        assert isinstance(cubexes, dict)
        assert len(cubexes) > 0

        # Required patterns exist
        required_patterns = [Goal.solved, Goal.cross, Goal.f2l]
        for pattern in required_patterns:
            assert pattern in cubexes
            assert isinstance(cubexes[pattern], Cubex)

    def test_get_cubexes_caching(self) -> None:
        """Test that get_cubexes uses caching."""
        cube_size = 3
        cubexes1 = get_cubexes(cube_size=cube_size)
        cubexes2 = get_cubexes(cube_size=cube_size)

        # Should be the same object due to LRU caching
        assert cubexes1 is cubexes2


class TestCubexEdgeCases:
    """Test edge cases for Cubex."""

    def test_empty_cubex(self) -> None:
        """Test creating empty cubex."""
        cubex = Cubex(patterns=[], names=[])
        assert len(cubex) == 0

    def test_cubex_match_with_empty_patterns(self) -> None:
        """Test matching with empty patterns list."""
        cubex = Cubex(patterns=[], names=[])
        permutation = get_rubiks_cube_state(MoveSequence())
        # Empty cubex should not match anything
        assert not cubex.match(permutation)

    def test_cubex_entropy_with_single_pattern(self) -> None:
        """Test entropy calculation with single pattern."""
        pattern = get_solved_pattern(cube_size=3)
        cubex = Cubex(patterns=[pattern], names=["test"])
        # Entropy should be finite and non-negative
        assert 0 <= cubex.entropy < float("inf")
