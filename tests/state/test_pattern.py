import numpy as np
import pytest

from rubiks_cube.configuration.type_definitions import CubePattern
from rubiks_cube.state.pattern import merge_patterns


def test_merge_patterns_single() -> None:
    patterns = [
        np.array([1, 1, 0, 0, 0, 0, 0, 0]),
        np.array([0, 0, 0, 0, 0, 0, 0, 0]),
    ]
    merged = merge_patterns(patterns=patterns)
    assert np.array_equal(merged, np.array([1, 1, 0, 0, 0, 0, 0, 0]))


def test_merge_patterns_duplicate() -> None:
    patterns = [
        np.array([1, 1, 0, 0, 0, 0, 0, 0]),
        np.array([1, 1, 0, 0, 0, 0, 0, 0]),
    ]
    merged = merge_patterns(patterns=patterns)
    assert np.array_equal(merged, np.array([1, 1, 0, 0, 0, 0, 0, 0]))


def test_merge_patterns_disjoint() -> None:
    patterns = [
        np.array([1, 1, 0, 0, 0, 0, 0, 0]),
        np.array([0, 0, 2, 2, 0, 0, 0, 0]),
    ]
    merged = merge_patterns(patterns=patterns)
    assert np.array_equal(merged, np.array([1, 1, 2, 2, 0, 0, 0, 0]))


def test_merge_patterns_disjoint_same() -> None:
    patterns = [
        np.array([1, 1, 0, 0, 0, 0, 0, 0]),
        np.array([0, 0, 1, 1, 0, 0, 0, 0]),
    ]
    merged = merge_patterns(patterns=patterns)
    assert np.array_equal(merged, np.array([1, 1, 2, 2, 0, 0, 0, 0]))


def test_merge_patterns_overlap() -> None:
    patterns = [
        np.array([1, 1, 0, 0, 0, 0, 0, 0]),
        np.array([0, 1, 1, 0, 0, 0, 0, 0]),
    ]
    merged = merge_patterns(patterns=patterns)
    assert np.array_equal(merged, np.array([1, 2, 3, 0, 0, 0, 0, 0]))


def test_merge_patterns_empty() -> None:
    patterns: list[CubePattern] = []
    with pytest.raises(ValueError):
        merge_patterns(patterns=patterns)


def test_merge_patterns_unequal_len() -> None:
    patterns = [
        np.array([1, 1, 0, 0, 0, 0, 0, 0]),
        np.array([0, 0, 1, 1, 0, 0, 0]),
    ]
    with pytest.raises(ValueError):
        merge_patterns(patterns=patterns)
