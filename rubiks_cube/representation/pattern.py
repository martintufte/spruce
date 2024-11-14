import logging
from collections.abc import Sequence
from functools import lru_cache
from math import factorial
from typing import Final

import numpy as np
from bidict import bidict
from bidict._exc import ValueDuplicationError

from rubiks_cube.configuration import CUBE_SIZE
from rubiks_cube.configuration.enumeration import Piece
from rubiks_cube.configuration.enumeration import Symmetry
from rubiks_cube.configuration.types import CubeMask
from rubiks_cube.configuration.types import CubePattern
from rubiks_cube.move.generator import MoveGenerator
from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.representation import get_rubiks_cube_state
from rubiks_cube.representation.mask import get_single_piece_mask
from rubiks_cube.representation.permutation import apply_moves_to_permutation
from rubiks_cube.representation.permutation import get_identity_permutation
from rubiks_cube.representation.symmetries import find_symmetry_groups
from rubiks_cube.representation.utils import invert

LOGGER: Final = logging.getLogger(__name__)


def get_empty_pattern(cube_size: int = CUBE_SIZE) -> CubePattern:
    """
    Return the empty pattern of the cube.

    Args:
        cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.

    Returns:
        CubePattern: Empty pattern.
    """
    assert 1 <= cube_size <= 10, "Size must be between 1 and 10."

    return np.zeros(6 * cube_size**2, dtype=int)


def get_solved_pattern(cube_size: int = CUBE_SIZE) -> CubePattern:
    """
    Get the default Rubik's cube pattern.

    Args:
        cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.

    Returns:
        CubePattern: The default Rubik's cube pattern.
    """
    assert 1 <= cube_size <= 10, "Size must be between 1 and 10."

    return np.arange(6 * cube_size**2, dtype=int) + 1


def mask2pattern(mask: CubeMask) -> CubePattern:
    """
    Convert a mask to a pattern.

    Args:
        mask (CubeMask): Mask.

    Returns:
        CubePattern: Pattern.
    """
    pattern: CubePattern = mask.astype(int)
    return pattern


def pattern2mask(pattern: CubePattern) -> CubeMask:
    """
    Convert a pattern to a mask.

    Args:
        pattern (CubePattern): Pattern.

    Returns:
        CubeMask: Mask.
    """
    mask: CubeMask = pattern != 0
    return mask


def generate_pattern_symmetries(
    initial_pattern: CubePattern,
    generator: MoveGenerator | None = None,
    max_size: int = 24,
    cube_size: int = CUBE_SIZE,
) -> list[CubePattern]:
    """Generate list of pattern symmetries of the cube using the generator.

    Args:
        initial_pattern (CubePattern): Cube pattern.
        generator (MoveGenerator, optional): Move generator. Defaults to MoveGenerator("<x, y>").
        max_size (int, optional): Max size of the symmetry group. Defaults to 24.
        cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.

    Raises:
        ValueError: Symmetries is too large.

    Returns:
        list[CubePattern]: List of pattern symmetries.
    """
    if generator is None:
        generator = MoveGenerator("<x, y>")

    identity = get_identity_permutation(cube_size=cube_size)
    permutations = [
        apply_moves_to_permutation(identity, sequence, cube_size=cube_size)
        for sequence in generator
    ]

    list_of_patterns: list[CubePattern] = [initial_pattern]
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


def generate_pattern_symmetries_from_subset(
    pattern: CubePattern,
    symmetry: Symmetry,
    prefix: str = "",
    cube_size: int = CUBE_SIZE,
) -> tuple[list[CubePattern], list[str]]:
    """
    Generate list of pattern symmetries of the cube using the subset as base.

    Args:
        pattern (CubePattern): Cube pattern.
        symmetry (Symmetry): Symmetry of the cube.
        prefix (str, optional): Prefix of the symmetry. Defaults to "".
        cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.

    Returns:
        tuple[list[CubePattern], list[str]]: List of pattern symmetries and their names.
    """
    symmetry_group = find_symmetry_groups(symmetry)

    identity = get_identity_permutation(cube_size=cube_size)
    offset = apply_moves_to_permutation(
        identity, MoveSequence(symmetry_group[symmetry]), cube_size=cube_size
    )

    list_of_patterns: list[CubePattern] = []
    list_of_names: list[str] = []

    for subset, seq in symmetry_group.items():
        permutation = apply_moves_to_permutation(
            invert(offset),
            sequence=MoveSequence(seq),
            cube_size=cube_size,
        )

        list_of_patterns.append(pattern[permutation])
        list_of_names.append(f"{prefix}-{subset.value}")

    return list_of_patterns, list_of_names


def pattern_from_generator(
    generator: MoveGenerator | None = None,
    mask: CubeMask | None = None,
    cube_size: int = CUBE_SIZE,
) -> CubePattern:
    """
    Generate a pattern from a generator.

    Args:
        generator (MoveGenerator, optional): Move generator. Defaults to MoveGenerator("<x, y>").
        mask (CubeMask | None, optional): Mask of pieces to generate a pattern on. Defaults to None.
        cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.

    Returns:
        CubePattern: Cube pattern.
    """
    if generator is None:
        generator = MoveGenerator("<x, y>")
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
    """
    Return True if the two patterns are equal.

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
    """
    Merge multiple patterns into one.

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


@lru_cache(maxsize=None)
def piece_masks(piece: Piece, cube_size: int = CUBE_SIZE) -> list[CubeMask]:
    """
    Generate the symmetries of a piece.

    Args:
        piece (Piece): Piece type.
        cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.

    Returns:
        list[CubePattern]: List of piece symmetries.
    """
    single_piece_mask = get_single_piece_mask(piece, cube_size=cube_size)
    single_piece_pattern = mask2pattern(single_piece_mask)
    symmetries = generate_pattern_symmetries(
        initial_pattern=single_piece_pattern,
        max_size=48,
        cube_size=cube_size,
    )
    return [pattern2mask(symmetry) for symmetry in symmetries]


def pattern_combinations(pattern: CubePattern, cube_size: int = CUBE_SIZE) -> int:
    """
    Calculate the combinations of a pattern. Assumes that the pattern is rotated.

    Args:
        pattern (CubePattern): Cube pattern.
        cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.

    Returns:
        float: Entropy of the pattern, equal to the Shannon entropy.
    """
    assert 1 <= cube_size <= 3, "Size must be between 1 and 3."

    combinations = piece_combinations(pattern, Piece.corner, cube_size)
    combinations *= piece_combinations(pattern, Piece.edge, cube_size)

    if combinations > 1 and not has_parity(cube_size):
        combinations //= 2

    return combinations


def piece_combinations(pattern: CubePattern, piece: Piece, cube_size: int = CUBE_SIZE) -> int:
    """Calculate the combinations of a piece in the pattern."""
    if cube_size == 1 or cube_size == 2 and piece == Piece.edge:
        return 1

    combinations = 1
    count_unique: dict[tuple[int, ...], int] = {}
    for mask in piece_masks(piece, cube_size=cube_size):
        cubies = pattern[mask]
        cubies.sort()
        cubies_tuple = tuple(cubies)
        if cubies_tuple not in count_unique:
            count_unique[cubies_tuple] = 1
        else:
            count_unique[cubies_tuple] += 1

    n_cubies = len(cubies)

    # Calculate the number of combinations for each unique piece tuple
    all_orientated = True
    for corner_tuple, count in count_unique.items():
        if count == 1:
            continue
        combinations *= factorial(count)
        if len(set(corner_tuple)) == 1:
            combinations *= n_cubies**count
            all_orientated = False

    # The last piece orientation is fixed by the rest
    if not all_orientated and combinations > 1:
        combinations //= n_cubies
    return combinations


def has_parity(cube_size: int) -> bool:
    """Check if the cube has parity."""
    return cube_size == 2 or cube_size > 3
