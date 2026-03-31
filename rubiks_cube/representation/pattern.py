from __future__ import annotations

import logging
from math import factorial
from typing import TYPE_CHECKING
from typing import Final

import numpy as np
from bidict import bidict
from bidict._exc import ValueDuplicationError

from rubiks_cube.configuration.enumeration import Variant
from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.representation import get_rubiks_cube_permutation
from rubiks_cube.representation.symmetries import find_variant_group

if TYPE_CHECKING:
    from collections.abc import Sequence

    from rubiks_cube.configuration.enumeration import Variant
    from rubiks_cube.configuration.types import MaskArray
    from rubiks_cube.configuration.types import PatternArray
    from rubiks_cube.move.generator import MoveGenerator
    from rubiks_cube.move.meta import MoveMeta

LOGGER: Final = logging.getLogger(__name__)


def get_empty_pattern(size: int) -> PatternArray:
    return np.zeros(size, dtype=int)


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
    """Calculate the number of combinations of a pattern using automatic piece discovery.

    Uses orbit analysis and the pieces property to identify permutable groups
    and their orientations, then calculates how many ways the pattern can be achieved.

    Args:
        pattern (PatternArray): Pattern array.
        move_meta (MoveMeta): Meta information about moves.

    Returns:
        int: Number of combinations.
    """
    combinations = calc_combinations(pattern, move_meta)

    # TODO: Verify that this is correct calculation
    if combinations > 1 and not move_meta.has_parity:
        assert combinations % 2 == 0
        return combinations // 2
    return combinations


def calc_combinations(pattern: PatternArray, move_meta: MoveMeta) -> int:
    """Calculate the combinations of pieces using blocks of imprimitivity and orbit analysis.

    Groups pieces by which positions they can reach (orbits under the base moves),
    then within each orbit counts arrangements based on pattern labels.
    A piece whose stickers all share one label has free orientation; distinct labels
    mean orientation is kept (tracked by the pattern).
    """
    pieces = move_meta.pieces
    if not pieces:
        return 1

    n_pieces = len(pieces)

    # Map every sticker index back to its piece index
    index_to_piece: dict[int, int] = {}
    for i, block in enumerate(pieces):
        for idx in block:
            index_to_piece[idx] = i

    # Build induced permutations on piece blocks from the non-substituted base moves
    base_moves = move_meta.base_moves - set(move_meta.substitutions)
    induced_perms: list[list[int]] = []
    for move in base_moves:
        perm = move_meta.permutations[move]
        induced = list(range(n_pieces))
        for piece_idx, block in enumerate(pieces):
            rep = next(iter(block))
            induced[piece_idx] = index_to_piece[int(perm[rep])]
        induced_perms.append(induced)

    # Union-find to group pieces into orbits (positions reachable from each other)
    parent = list(range(n_pieces))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x: int, y: int) -> None:
        px, py = find(x), find(y)
        if px != py:
            parent[px] = py

    for induced in induced_perms:
        for i, j in enumerate(induced):
            if i != j:
                union(i, j)

    # Collect piece indices per orbit
    orbit_to_pieces: dict[int, list[int]] = {}
    for i in range(n_pieces):
        orbit_to_pieces.setdefault(find(i), []).append(i)

    combinations = 1

    for orbit_piece_indices in orbit_to_pieces.values():
        n_stickers = len(pieces[orbit_piece_indices[0]])
        count_unique: dict[tuple[int, ...], int] = {}

        for piece_idx in orbit_piece_indices:
            block = pieces[piece_idx]
            # Sort sticker values to normalise orientation for grouping
            signature = tuple(sorted(pattern[sorted(block)]))
            count_unique[signature] = count_unique.get(signature, 0) + 1

        orbit_combinations = 1
        all_oriented = True

        for signature, count in count_unique.items():
            if count <= 1:
                continue
            orbit_combinations *= factorial(count)
            # All stickers share the same label → orientation is free
            if len(set(signature)) == 1:
                orbit_combinations *= n_stickers**count
                all_oriented = False

        # Within each orbit the last free orientation is fixed by the others
        if not all_oriented and orbit_combinations > 1:
            orbit_combinations //= n_stickers

        combinations *= orbit_combinations

    return combinations
