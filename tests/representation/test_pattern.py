from __future__ import annotations

from math import factorial
from typing import TYPE_CHECKING

import numpy as np
import pytest

from rubiks_cube.autotagger import get_rubiks_cube_pattern
from rubiks_cube.autotagger.cubex import Cubex
from rubiks_cube.configuration.enumeration import Goal
from rubiks_cube.configuration.enumeration import Symmetry
from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.representation.pattern import generate_pattern_symmetries_from_subset
from rubiks_cube.representation.pattern import merge_patterns
from rubiks_cube.representation.pattern import pattern_combinations
from rubiks_cube.representation.pattern import pattern_implies

if TYPE_CHECKING:
    from rubiks_cube.configuration.types import CubePattern


class TestMergePatterns:
    def test_merge_patterns_single(self) -> None:
        patterns = [
            np.array([1, 1, 0, 0, 0, 0, 0, 0]),
            np.array([0, 0, 0, 0, 0, 0, 0, 0]),
        ]
        merged = merge_patterns(patterns=patterns)
        assert np.array_equal(merged, np.array([1, 1, 0, 0, 0, 0, 0, 0]))

    def test_merge_patterns_duplicate(self) -> None:
        patterns = [
            np.array([1, 1, 0, 0, 0, 0, 0, 0]),
            np.array([1, 1, 0, 0, 0, 0, 0, 0]),
        ]
        merged = merge_patterns(patterns=patterns)
        assert np.array_equal(merged, np.array([1, 1, 0, 0, 0, 0, 0, 0]))

    def test_merge_patterns_disjoint(self) -> None:
        patterns = [
            np.array([1, 1, 0, 0, 0, 0, 0, 0]),
            np.array([0, 0, 2, 2, 0, 0, 0, 0]),
        ]
        merged = merge_patterns(patterns=patterns)
        assert np.array_equal(merged, np.array([1, 1, 2, 2, 0, 0, 0, 0]))

    def test_merge_patterns_disjoint_same(self) -> None:
        patterns = [
            np.array([1, 1, 0, 0, 0, 0, 0, 0]),
            np.array([0, 0, 1, 1, 0, 0, 0, 0]),
        ]
        merged = merge_patterns(patterns=patterns)
        assert np.array_equal(merged, np.array([1, 1, 2, 2, 0, 0, 0, 0]))

    def test_merge_patterns_overlap(self) -> None:
        patterns = [
            np.array([1, 1, 0, 0, 0, 0, 0, 0]),
            np.array([0, 1, 1, 0, 0, 0, 0, 0]),
        ]
        merged = merge_patterns(patterns=patterns)
        assert np.array_equal(merged, np.array([1, 2, 3, 0, 0, 0, 0, 0]))

    def test_merge_patterns_empty(self) -> None:
        patterns: list[CubePattern] = []
        with pytest.raises(ValueError):
            merge_patterns(patterns=patterns)

    def test_merge_patterns_unequal_len(self) -> None:
        patterns = [
            np.array([1, 1, 0, 0, 0, 0, 0, 0]),
            np.array([0, 0, 1, 1, 0, 0, 0]),
        ]
        with pytest.raises(ValueError):
            merge_patterns(patterns=patterns)


class TestPatternImplies:
    def test_pattern_implies_identical(self) -> None:
        pattern = np.array([1, 1, 0, 0, 0, 0, 0, 0])
        subset = np.array([1, 1, 0, 0, 0, 0, 0, 0])
        assert pattern_implies(pattern, subset)

    def test_pattern_implies_reindex(self) -> None:
        pattern = np.array([1, 1, 0, 0, 0, 0, 0, 0])
        subset = np.array([2, 2, 0, 0, 0, 0, 0, 0])
        assert pattern_implies(pattern, subset)

    def test_pattern_implies_empty(self) -> None:
        pattern = np.array([1, 1, 0, 0, 0, 0, 0, 0])
        subset = np.array([0, 0, 0, 0, 0, 0, 0, 0])
        assert pattern_implies(pattern, subset)

    def test_pattern_implies_slacker(self) -> None:
        pattern = np.array([1, 1, 2, 2, 0, 0, 0, 0])
        subset = np.array([1, 1, 1, 1, 0, 0, 0, 0])
        assert pattern_implies(pattern, subset)

    def test_pattern_not_implies_stricter(self) -> None:
        pattern = np.array([1, 1, 1, 1, 0, 0, 0, 0])
        subset = np.array([1, 1, 2, 2, 0, 0, 0, 0])
        assert not pattern_implies(pattern, subset)

    def test_pattern_not_implies_disjoint(self) -> None:
        pattern = np.array([1, 1, 0, 0, 0, 0, 0, 0])
        subset = np.array([0, 0, 1, 1, 0, 0, 0, 0])
        assert not pattern_implies(pattern, subset)

    def test_pattern_not_implies_from_empty(self) -> None:
        pattern = np.array([0, 0, 0, 0, 0, 0, 0, 0])
        subset = np.array([1, 1, 0, 0, 0, 0, 0, 0])
        assert not pattern_implies(pattern, subset)


class TestPatternCombinations:
    def test_pattern_combinations_solved(self) -> None:
        cube_size = 3
        pattern = get_rubiks_cube_pattern(goal=Goal.solved, cube_size=cube_size)
        n_combinations = pattern_combinations(pattern=pattern, cube_size=cube_size)
        assert n_combinations == 1

    def test_pattern_combinations_none(self) -> None:
        cube_size = 3
        pattern = get_rubiks_cube_pattern(goal=Goal.none, cube_size=cube_size)
        n_combinations = pattern_combinations(pattern=pattern, cube_size=cube_size)
        assert n_combinations == factorial(8) * 3**7 * factorial(12) * 2**11 / 2

    def test_pattern_combinations_eo(self) -> None:
        cube_size = 3
        pattern = get_rubiks_cube_pattern(goal=Goal.eo, subset="eo-fb", cube_size=cube_size)
        n_combinations = pattern_combinations(pattern=pattern, cube_size=cube_size)
        assert n_combinations == factorial(8) * 3**7 * factorial(12) / 2

    def test_pattern_combinations_dr(self) -> None:
        cube_size = 3
        pattern = get_rubiks_cube_pattern(goal=Goal.dr_ud, cube_size=cube_size)
        n_combinations = pattern_combinations(pattern=pattern, cube_size=cube_size)
        assert n_combinations == factorial(8) * factorial(8) * factorial(4) / 2

    def test_pattern_combinations_cross(self) -> None:
        cube_size = 3
        pattern = get_rubiks_cube_pattern(goal=Goal.cross, subset="cross-down", cube_size=cube_size)
        n_combinations = pattern_combinations(pattern=pattern, cube_size=cube_size)
        assert n_combinations == factorial(8) * 3**7 * factorial(8) * 2**7 / 2


class TestGeneratePatternsFromSubset:
    def test_generate_patterns_from_subset(self) -> None:
        cube_size = 3
        cubex = Cubex.from_settings(
            name=Goal.cross.value,
            solved_sequence=MoveSequence("R L U2 R2 L2 U2 R L U"),
            symmetry=Symmetry.down,
            cube_size=cube_size,
        )

        patterns, names = generate_pattern_symmetries_from_subset(
            pattern=cubex.patterns[0],
            symmetry=Symmetry.down,
            prefix="cross",
            cube_size=cube_size,
        )

        assert len(patterns) == 6
        assert len(names) == 6
