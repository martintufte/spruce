from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from collections.abc import Sequence

    from spruce.types import IndexArray
    from spruce.types import PatternArray
    from spruce.types import PermutationArray


def get_empty_pattern(size: int) -> PatternArray:
    return np.zeros(size, dtype=int)


def get_identity_pattern(size: int) -> PatternArray:
    pattern = np.arange(size, dtype=int) + 1
    return pattern.astype(dtype=np.uint)


def find_orbit_labels(
    permutations: Sequence[PermutationArray],
    size: int,
) -> IndexArray:
    """Label each index with the smallest index in its orbit under the permutations.

    Uses vectorized min-label propagation to a fixpoint.
    """
    labels = np.arange(size)
    while True:
        new_labels = labels
        for permutation in permutations:
            # Link every index with the index it maps to. Aliasing new_labels as both
            # operand and output of minimum.at is safe: labels only ever decrease within
            # an orbit, and the outer loop runs to a fixpoint.
            new_labels = np.minimum(new_labels, new_labels[permutation])
            np.minimum.at(new_labels, permutation, new_labels)
        # Pointer jumping: compress label chains toward the orbit minimum
        new_labels = new_labels[new_labels]
        if np.array_equal(new_labels, labels):
            return labels
        labels = new_labels


def pattern_equivalent(pattern: PatternArray, other_pattern: PatternArray) -> bool:
    """Return True if the two patterns are equivalent, i.e. if there is a bijection between them.

    Note: The empty label is always mapped to the empty label.

    Args:
        pattern (PatternArray): First pattern.
        other_pattern (PatternArray): Second pattern.

    Returns:
        bool: Whether the two patterns are equal.
    """
    if pattern.shape != other_pattern.shape:
        return False

    forward: dict[int, int] = {0: 0}
    reverse: dict[int, int] = {0: 0}
    for idx1, idx2 in zip(pattern, other_pattern, strict=True):
        if forward.setdefault(idx1, idx2) != idx2 or reverse.setdefault(idx2, idx1) != idx1:
            return False

    return True


def pattern_implies(pattern: PatternArray, other_pattern: PatternArray) -> bool:
    """Return True if the pattern implies the other pattern.

    Args:
        pattern (PatternArray): Goal.
        other_pattern (PatternArray): Other pattern.

    Returns:
        bool: Whether the pattern implies the other pattern.
    """
    if pattern.shape != other_pattern.shape:
        return False

    mapping: dict[int, int] = {0: 0}
    for idx1, idx2 in zip(pattern, other_pattern, strict=True):
        if idx1 in mapping and mapping[idx1] != idx2:
            return False
        mapping[idx1] = idx2

    return True


def merge_patterns(patterns: Sequence[PatternArray]) -> PatternArray:
    """Merge multiple patterns into one.

    Args:
        patterns (Sequence[PatternArray]): Sequence of patterns.

    Raises:
        ValueError: No patterns found.

    Returns:
        PatternArray: Merged pattern.
    """
    for pattern in patterns:
        merged_pattern = np.zeros_like(pattern)
        break
    else:
        raise ValueError("No patterns found.")

    new_color_map: dict[tuple[int, ...], int] = {}
    for i, x in enumerate(zip(*patterns, strict=True)):
        if all(pattern_val == 0 for pattern_val in x):
            continue
        elif x in new_color_map:
            merged_pattern[i] = new_color_map[x]
        else:
            new_color_map[x] = merged_pattern[i] = len(new_color_map) + 1

    return merged_pattern
