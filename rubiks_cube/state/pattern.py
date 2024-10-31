import logging
from collections.abc import Sequence
from typing import Final

import numpy as np
from bidict import bidict
from bidict._exc import ValueDuplicationError

from rubiks_cube.configuration import CUBE_SIZE
from rubiks_cube.configuration.types import CubeMask
from rubiks_cube.configuration.types import CubePattern
from rubiks_cube.move.generator import MoveGenerator
from rubiks_cube.state import get_rubiks_cube_state
from rubiks_cube.state.permutation import apply_moves_to_state
from rubiks_cube.state.permutation import get_identity_permutation

LOGGER: Final = logging.getLogger(__name__)


def get_empty_pattern(cube_size: int = CUBE_SIZE) -> CubePattern:
    """Return the empty pattern of the cube.

    Args:
        cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.

    Returns:
        CubePattern: Empty pattern.
    """

    assert 1 <= cube_size <= 10, "Size must be between 1 and 10."

    return np.zeros(6 * cube_size**2, dtype=int)


def get_solved_pattern(cube_size: int = CUBE_SIZE) -> CubePattern:
    """Get the default Rubik's cube pattern.

    Args:
        cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.

    Returns:
        CubePattern: The default Rubik's cube pattern.
    """

    assert 1 <= cube_size <= 10, "Size must be between 1 and 10."

    return np.arange(6 * cube_size**2, dtype=int) + 1


def generate_symmetries(
    pattern: CubePattern,
    generator: MoveGenerator = MoveGenerator("<x, y>"),
    max_size: int = 24,
    cube_size: int = CUBE_SIZE,
) -> list[CubePattern]:
    """Generate list of pattern symmetries of the cube using the generator.

    Args:
        pattern (CubePattern): Cube pattern.
        generator (MoveGenerator, optional): Move generator. Defaults to MoveGenerator("<x, y>").
        max_size (int, optional): Max size of the symmetry group. Defaults to 24.
        cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.

    Raises:
        ValueError: Symmetries is too large.

    Returns:
        list[CubePattern]: List of pattern symmetries.
    """

    identity = get_identity_permutation(cube_size=cube_size)
    permutations = [
        apply_moves_to_state(identity, sequence, cube_size=cube_size) for sequence in generator
    ]

    list_of_patterns: list[CubePattern] = [pattern]
    size = len(list_of_patterns)

    while True:
        for pattern in list_of_patterns:
            for permutation in permutations:
                new_pattern: CubePattern = pattern[permutation]
                if not any(
                    pattern_equal(new_pattern, current_pattern)
                    for current_pattern in list_of_patterns
                ):
                    list_of_patterns.append(new_pattern)
        if len(list_of_patterns) == size:
            break
        size = len(list_of_patterns)
        if size > max_size:
            raise ValueError(f"Symmetries is too large, {len(list_of_patterns)} > {max_size}!")

    return list_of_patterns


def pattern_from_generator(
    generator: MoveGenerator = MoveGenerator("<x, y>"),
    mask: CubeMask | None = None,
    cube_size: int = CUBE_SIZE,
) -> CubePattern:
    """Generate a pattern from a generator.

    Args:
        generator (MoveGenerator, optional): Move generator. Defaults to MoveGenerator("<x, y>").
        mask (CubeMask | None, optional): Mask of pieces to generate a pattern on. Defaults to None.
        cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.

    Returns:
        CubePattern: Cube pattern.
    """
    if mask is None:
        mask = np.ones(6 * cube_size**2, dtype=bool)

    permutations = [
        get_rubiks_cube_state(sequence=sequence, cube_size=cube_size) for sequence in generator
    ]

    # Initialize pattern as zeros everywhere, and orientations as 1, 2, 3, ...
    pattern = get_identity_permutation(cube_size=cube_size) + 1
    pattern[~mask] = 0

    for permutation in permutations:
        for i, j in zip(pattern, pattern[permutation]):
            if i != j:
                pattern[pattern == j] = i

    return pattern


def pattern_equal(pattern1: CubePattern, pattern2: CubePattern) -> bool:
    """Return True if the two patterns are equal.

    Args:
        pattern1 (CubePattern): First pattern.
        pattern2 (CubePattern): Second pattern.

    Returns:
        bool: Whether the two patterns are equal.
    """
    if pattern1.shape != pattern2.shape:
        return False

    mapping: bidict[int, int] = bidict()
    try:
        for idx1, idx2 in zip(pattern1, pattern2, strict=True):
            if idx1 in mapping and mapping[idx1] != idx2:
                return False
            mapping[idx1] = idx2

    except ValueDuplicationError:
        return False

    return True


def merge_patterns(patterns: Sequence[CubePattern]) -> CubePattern:
    """Merge multiple patterns into one.

    Args:
        patterns (list[CubePattern]): List of patterns.

    Raises:
        ValueError: No patterns found.

    Returns:
        CubePattern: Merged pattern.
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


def pattern_entropy(pattern: CubePattern) -> float:
    """Calculate the entropy of a pattern.

    Args:
        pattern (CubePattern): Cube pattern.

    Returns:
        float: Entropy of the pattern, equal to the Shannon entropy.
            Currently, the function estimates the entropy by counting the number of unique elements.
    """
    return len(pattern) - len(np.unique(pattern))
