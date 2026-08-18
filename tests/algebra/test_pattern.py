from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import pytest

from spruce.algebra.pattern import merge_patterns
from spruce.algebra.pattern import pattern_implies

if TYPE_CHECKING:
    from spruce.types import PatternArray


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
        patterns: list[PatternArray] = []
        with pytest.raises(ValueError, match="No patterns found"):
            merge_patterns(patterns=patterns)

    def test_merge_patterns_unequal_len(self) -> None:
        patterns = [
            np.array([1, 1, 0, 0, 0, 0, 0, 0]),
            np.array([0, 0, 1, 1, 0, 0, 0]),
        ]
        with pytest.raises(ValueError, match="zip"):
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
