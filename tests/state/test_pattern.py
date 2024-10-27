import numpy as np
import pytest

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


def test_merge_patterns_overlap() -> None:
    patterns = [
        np.array([1, 1, 0, 0, 0, 0, 0, 0]),
        np.array([0, 2, 2, 0, 0, 0, 0, 0]),
    ]
    merged = merge_patterns(patterns=patterns)
    assert np.array_equal(merged, np.array([1, 1, 1, 0, 0, 0, 0, 0]))


def test_merge_patterns_inconsistent() -> None:
    patterns = [
        np.array([1, 1, 3, 3, 0, 0, 0, 0]),
        np.array([0, 2, 2, 0, 0, 0, 0, 0]),
    ]
    with pytest.raises(ValueError):
        merge_patterns(patterns=patterns)
