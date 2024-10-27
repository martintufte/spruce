import logging
from collections.abc import Sequence
from typing import Final

import numpy as np

from rubiks_cube.configuration import CUBE_SIZE
from rubiks_cube.configuration.type_definitions import CubeMask
from rubiks_cube.configuration.type_definitions import CubePattern
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

    return (np.arange(6 * cube_size**2, dtype=int) // cube_size**2).astype(int) + 1


def generate_symmetries(
    patterns: tuple[CubeMask, CubePattern],
    generator: MoveGenerator = MoveGenerator("<x, y>"),
    max_size: int = 24,
    cube_size: int = CUBE_SIZE,
) -> list[tuple[CubeMask, CubePattern]]:
    """Generate list of pattern symmetries of the cube using the generator.

    Args:
        patterns (tuple[CubeMask, CubePattern]): List of masks.
        generator (MoveGenerator, optional): Move generator. Defaults to MoveGenerator("<x, y>").
        max_size (int, optional): Max size of the symmetry group. Defaults to 60.
        cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.

    Raises:
        ValueError: Symmetries is too large.

    Returns:
        list[list[CubePattern]]: List of pattern symmetries.
    """

    identity = get_identity_permutation(cube_size=cube_size)
    permutations = [
        apply_moves_to_state(identity, sequence, cube_size=cube_size) for sequence in generator
    ]

    list_of_patterns: list[tuple[CubeMask, CubePattern]] = [patterns]
    size = len(list_of_patterns)

    while True:
        for patterns in list_of_patterns:
            for permutation in permutations:
                new_patterns: tuple[CubeMask, CubePattern] = (
                    patterns[0][permutation],
                    patterns[1][permutation],
                )
                if not any(
                    all(
                        np.array_equal(new_pattern, current_pattern)
                        for new_pattern, current_pattern in zip(new_patterns, current_patterns)
                    )
                    for current_patterns in list_of_patterns
                ):
                    list_of_patterns.append(new_patterns)
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
