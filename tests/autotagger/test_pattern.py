from __future__ import annotations

from rubiks_cube.autotagger.pattern import Pattern
from rubiks_cube.autotagger.pattern import get_patterns
from rubiks_cube.configuration.enumeration import Goal
from rubiks_cube.configuration.enumeration import Variant
from rubiks_cube.move.meta import MoveMeta
from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.representation import get_rubiks_cube_permutation
from rubiks_cube.representation.pattern import get_empty_pattern
from rubiks_cube.representation.pattern import get_identity_pattern
from rubiks_cube.representation.permutation import get_identity_permutation


class TestPatternBasics:
    def test_pattern_initialization(self) -> None:
        """Test Pattern initialization."""
        pattern = get_identity_pattern(cube_size=3)
        pattern = Pattern(variants={Variant.none: pattern})
        assert len(pattern) == 1

    def test_pattern_repr(self) -> None:
        """Test Pattern string representation."""
        pattern = get_identity_pattern(cube_size=3)
        pattern = Pattern(variants={Variant.none: pattern})
        repr_str = repr(pattern)
        assert "Pattern" in repr_str
        assert "variants" in repr_str


class TestPatternOperations:
    def test_pattern_and_operation(self) -> None:
        """Test AND operation between Patternes."""
        pattern1 = get_identity_pattern(cube_size=3)
        pattern2 = get_identity_pattern(cube_size=3)
        pattern1 = Pattern(variants={Variant.none: pattern1})
        pattern2 = Pattern(variants={Variant.none: pattern2})

        result = pattern1 & pattern2
        assert len(result) >= 1  # At least one merged pattern

    def test_pattern_contains_self(self) -> None:
        """Test that pattern contains itself."""
        pattern = get_identity_pattern(cube_size=3)
        pattern1 = Pattern(variants={Variant.none: pattern})
        pattern2 = Pattern(variants={Variant.none: pattern})
        assert pattern1 in pattern2

    def test_pattern_contains_invalid_type(self) -> None:
        """Test that contains returns False for invalid types."""
        pattern = get_identity_pattern(cube_size=3)
        pattern = Pattern(variants={Variant.none: pattern})
        # Contains checks for Pattern type, so these will return False
        assert "invalid" not in pattern
        assert 42 not in pattern


class TestPatternMatch:
    def test_match_solved_cube(self) -> None:
        """Test matching solved cube."""
        pattern = get_identity_pattern(cube_size=3)
        pattern = Pattern(variants={Variant.none: pattern})
        permutation = get_identity_permutation(cube_size=3)
        assert pattern.match(permutation) is not None

    def test_no_match_scrambled_cube(self) -> None:
        """Test that solved pattern doesn't match scrambled cube."""
        move_meta = MoveMeta.from_cube_size(3)
        pattern = get_identity_pattern(cube_size=3)
        pattern = Pattern(variants={Variant.none: pattern})
        permutation = get_rubiks_cube_permutation(MoveSequence.from_str("U"), move_meta)
        assert pattern.match(permutation) is None

    def test_match_with_multiple_patterns(self) -> None:
        """Test matching with multiple patterns."""
        pattern1 = get_identity_pattern(cube_size=3)
        pattern2 = get_empty_pattern(cube_size=3)
        pattern = Pattern(variants={Variant.front: pattern1, Variant.back: pattern2})

        # Solved cube should match first pattern
        permutation = get_identity_permutation(cube_size=3)
        assert pattern.match(permutation) is not None


class TestPatternProperties:
    move_meta: MoveMeta = MoveMeta.from_cube_size(3)

    def test_combinations_and_entropy(self) -> None:
        """Test combinations and entropy properties together."""
        pattern = get_identity_pattern(cube_size=3)
        pattern = Pattern(variants={Variant.none: pattern})

        # Test combinations
        combinations = pattern.calc_combinations(move_meta=self.move_meta)
        assert isinstance(combinations, int)
        assert combinations > 0

        # Test entropy
        entropy = pattern.entropy(move_meta=self.move_meta)
        assert isinstance(entropy, float)
        assert entropy >= 0


class TestPatternContains:
    def test_dr_contains_eo(self) -> None:
        """Test that DR contains EO."""
        cube_size = 3
        patterns = get_patterns(cube_size=cube_size)

        assert patterns[Goal.eo] in patterns[Goal.dr]
        assert patterns[Goal.dr] not in patterns[Goal.eo]

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
    move_meta: MoveMeta = MoveMeta.from_cube_size(3)

    def test_empty_pattern(self) -> None:
        """Test creating empty pattern."""
        pattern = Pattern(variants={})
        assert len(pattern) == 0

    def test_pattern_match_with_empty_patterns(self) -> None:
        """Test matching with empty patterns list."""
        pattern = Pattern(variants={})
        permutation = get_rubiks_cube_permutation(MoveSequence(), move_meta=self.move_meta)
        # Empty pattern should not match anything
        assert pattern.match(permutation) is None

    def test_pattern_entropy_with_single_pattern(self) -> None:
        """Test entropy calculation with single pattern."""
        pattern = get_identity_pattern(cube_size=3)
        pattern = Pattern(variants={Variant.none: pattern})
        # Entropy should be finite and non-negative
        assert 0 <= pattern.entropy(self.move_meta) < float("inf")


class TestGetPatternsExpected:
    patterns = get_patterns(cube_size=3)
    move_meta = MoveMeta.from_cube_size(3)

    def test_solved_pattern(self) -> None:
        """Test retrieving solved pattern."""
        pattern = self.patterns.get(Goal.solved)
        assert pattern is not None
        assert len(pattern) == 1
        assert next(iter(pattern.variants.values())).size == self.move_meta.size

    def test_cross_pattern(self) -> None:
        """Test retrieving cross pattern."""
        pattern = self.patterns.get(Goal.cross)
        assert pattern is not None
        assert len(pattern) == 6
        assert next(iter(pattern.variants.values())).size == self.move_meta.size

    def test_f2l_pattern(self) -> None:
        """Test retrieving F2L pattern."""
        pattern = self.patterns.get(Goal.f2l)
        assert pattern is not None
        assert len(pattern) == 6
        assert next(iter(pattern.variants.values())).size == self.move_meta.size

    def test_none_pattern(self) -> None:
        """Test retrieving empty/none pattern."""
        pattern = self.patterns.get(Goal.none)
        assert pattern is not None
        assert len(pattern) == 1
        assert next(iter(pattern.variants.values())).size == self.move_meta.size
        # Empty pattern should be all zeros
        assert (next(iter(pattern.variants.values())) == 0).all()

    def test_pattern_matches_permutation(self) -> None:
        """Test that solved pattern matches identity permutation."""
        pattern = self.patterns.get(Goal.solved)
        assert pattern is not None
        permutation = get_rubiks_cube_permutation(MoveSequence(), move_meta=self.move_meta)
        assert pattern.match(permutation) is not None

    def test_pattern_does_not_match_scrambled(self) -> None:
        """Test that solved pattern doesn't match scrambled cube."""
        pattern = self.patterns.get(Goal.solved)
        assert pattern is not None
        permutation = get_rubiks_cube_permutation(
            MoveSequence.from_str("R U R' U'"), move_meta=self.move_meta
        )
        # Pattern should not match scrambled cube.
        # This test might need adjustment based on actual moves
        assert not pattern.match(permutation)
