from __future__ import annotations

import logging
from math import factorial
from typing import TYPE_CHECKING
from typing import Final

import numpy as np
from bidict import bidict
from bidict._exc import ValueDuplicationError

from rubiks_cube.configuration.enumeration import Piece
from rubiks_cube.configuration.enumeration import Variant
from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.representation import get_rubiks_cube_permutation
from rubiks_cube.representation.mask import piece_masks
from rubiks_cube.representation.symmetries import find_variant_group

if TYPE_CHECKING:
    from collections.abc import Sequence

    from rubiks_cube.configuration.types import MaskArray
    from rubiks_cube.configuration.types import PatternArray
    from rubiks_cube.move.generator import MoveGenerator
    from rubiks_cube.move.meta import MoveMeta

LOGGER: Final = logging.getLogger(__name__)


def get_empty_pattern(cube_size: int) -> PatternArray:
    return np.zeros(6 * cube_size**2, dtype=int)


def get_identity_pattern(size: int) -> PatternArray:
    pattern = np.arange(size, dtype=int) + 1
    return pattern.astype(dtype=np.uint)


def get_solved_pattern(cube_size: int) -> PatternArray:
    pattern = (np.arange(6 * cube_size**2, dtype=int) // cube_size**2) + 1
    return pattern.astype(dtype=np.uint)


def generate_pattern_variants(
    pattern: PatternArray,
    initial_variant: Variant,
    move_meta: MoveMeta,
) -> dict[Variant, PatternArray]:
    """Generate variants of pattern symmetries.

    Args:
        pattern (PatternArray): Initial pattern.
        initial_variant (Variant): Initial variant.
        move_meta (MoveMeta): Meta information about moves.

    Returns:
        dict[Variant, PatternArray]: Dictionary of variants.
    """
    variant_group = find_variant_group(initial_variant)

    inv_initial_permutation = get_rubiks_cube_permutation(
        sequence=MoveSequence(normal=variant_group[initial_variant]),
        move_meta=move_meta,
        invert_after=True,
    )

    out_variants: dict[Variant, PatternArray] = {}

    for variant, moves in variant_group.items():
        permutation_variant = get_rubiks_cube_permutation(
            sequence=MoveSequence(normal=moves),
            move_meta=move_meta,
            initial_permutation=inv_initial_permutation,
        )

        out_variants[variant] = pattern[permutation_variant]

    return out_variants


def pattern_from_generator(
    generator: MoveGenerator,
    move_meta: MoveMeta,
    mask: MaskArray | None = None,
) -> PatternArray:
    """Create a pattern from a generator.

    Args:
        generator (MoveGenerator): Move generator.
        move_meta (MoveMeta): Meta information about moves.
        mask (MaskArray | None, optional): Mask of pieces to generate a pattern on. Defaults to None.

    Returns:
        PatternArray: Cube pattern.
    """
    if mask is None:
        mask = np.ones(move_meta.size, dtype=bool)

    permutations = [
        get_rubiks_cube_permutation(sequence=sequence, move_meta=move_meta)
        for sequence in generator
    ]

    # Initialize pattern as zeros everywhere, and orientations as 1, 2, 3, ...
    pattern = get_identity_pattern(size=move_meta.size)
    pattern[~mask] = 0

    for permutation in permutations:
        for i, j in zip(pattern, pattern[permutation], strict=True):
            if i != j:
                pattern[pattern == j] = i

    return pattern


def pattern_equivalent(pattern: PatternArray, other_pattern: PatternArray) -> bool:
    """Return True if the two patterns are equivalent, i.e. if there is a bijection between them.

    Note: The empty cubie is always mapped to the empty cubie.

    Args:
        pattern (PatternArray): First pattern.
        other_pattern (PatternArray): Second pattern.

    Returns:
        bool: Whether the two patterns are equal.
    """
    if pattern.shape != other_pattern.shape:
        return False

    mapping: bidict[int, int] = bidict({0: 0})
    try:
        for idx1, idx2 in zip(pattern, other_pattern, strict=True):
            if idx1 in mapping and mapping[idx1] != idx2:
                return False
            mapping[idx1] = idx2

    except ValueDuplicationError:
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


def pattern_combinations(pattern: PatternArray, move_meta: MoveMeta) -> int:
    """Calculate the combinations of a pattern. Assumes that the pattern is rotated.

    Args:
        pattern (PatternArray): Cube pattern.
        move_meta (MoveMeta): Meta information about moves.

    Returns:
        float: Entropy of the pattern, equal to the Shannon entropy.
    """
    assert 1 <= move_meta.cube_size <= 3, "Size must be between 1 and 3."

    corner_combinations = piece_combinations(pattern, Piece.corner, move_meta)
    edge_combinations = piece_combinations(pattern, Piece.edge, move_meta)

    combinations = corner_combinations * edge_combinations

    # TODO: Verify that this is correct calculation
    if combinations > 1 and not move_meta.has_parity:
        assert combinations % 2 == 0
        return combinations // 2
    return combinations


# TODO: This might not work for centers
def piece_combinations(pattern: PatternArray, piece: Piece, move_meta: MoveMeta) -> int:
    """Calculate the combinations of a piece in the pattern."""
    cube_size = move_meta.cube_size

    if cube_size == 1 or (cube_size == 2 and piece == Piece.edge):
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
