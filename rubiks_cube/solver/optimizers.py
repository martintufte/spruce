from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import numpy as np

from rubiks_cube.configuration import CUBE_SIZE
from rubiks_cube.configuration.enumeration import Piece
from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.state import get_rubiks_cube_state
from rubiks_cube.state.permutation import get_piece_mask
from rubiks_cube.state.permutation import unorientate_mask
from rubiks_cube.state.utils import infer_cube_size
from rubiks_cube.state.utils import invert
from rubiks_cube.state.utils import reindex
from rubiks_cube.state.utils import reindex_new

if TYPE_CHECKING:
    from rubiks_cube.configuration.type_definitions import CubeMask
    from rubiks_cube.configuration.type_definitions import CubePermutation
    from rubiks_cube.configuration.type_definitions import CubeState


LOGGER = logging.getLogger(__name__)


class IndexOptimizer:
    """Sklearn style transformer to optimize indecies of cube permutations."""

    mask: CubeMask | None = None

    def fit_transform(
        self,
        actions: dict[str, CubePermutation],
        pattern: CubeState,
    ) -> tuple[dict[str, CubePermutation], CubeState]:
        """Fit the index optimizer to the permutations in the action space and cueb pattern.

        Args:
            actions (dict[str, CubePermutation]): Action space.
            pattern (CubeState): Cube pattern.
        """
        actions, pattern, self.mask = optimize_indecies(actions, pattern)
        return actions, pattern

    def transform(self, perm: CubePermutation) -> CubePermutation:
        """Transform the permutation using the mask.

        Args:
            perm (CubePermutation): Initial permutation.

        Returns:
            CubePermutation: Transformed permutation.
        """
        assert self.mask is not None
        return reindex_new(perm, self.mask)


# TODO: Permutation indecies optimizations:
# - Remove indecies not affected by the action space (DONE)
# - Remove indecies of conserved orientations of edges and corners (DONE)
# - Remove indecies from pieces that are not in the pattern (DONE)
# - Remvoe indecies of pieces that are always relatively solved wrt each other (DONE)
def optimize_indecies(
    actions: dict[str, CubePermutation],
    pattern: CubeState,
    cube_size: int = CUBE_SIZE,
) -> tuple[dict[str, CubePermutation], CubeState, CubeMask]:
    """Reduce the complexity of the permutations and action space.

    1. Identify indecies that are not affected by the action space.
    2. Identify conserved orientations of corners and edges.
    3. Identify piece types that are not in the pattern.
    4. Reindex the permutations and action space.
    5. Split into disjoint action groups and remove bijections
    6. Reindex the permutations and action space.

    Args:
        actions (dict[str, CubePermutation]): Action space.
        pattern (CubeState): Cube pattern.

    Returns:
        tuple[dict[str, CubePermutation], CubeState]: Optimized
            action space and pattern that can be used equivalently by the solver.
    """
    # This is a boolean mask that will be used to remove indecies
    boolean_mask = np.zeros_like(pattern, dtype=bool)

    # 1. Identify the indexes that are not affected by the action space
    identity = np.arange(len(pattern))
    for permutation in actions.values():
        boolean_mask |= identity != permutation

    # 2. Identify conserved orientations of corners and edges
    for piece in [Piece.corner, Piece.edge]:
        piece_mask = get_piece_mask(piece, cube_size=cube_size)
        union_mask = boolean_mask & piece_mask

        while np.any(union_mask):
            # Initialize a mask for the first piece in the union mask
            mask = np.zeros_like(identity, dtype=bool)
            mask[np.argmax(union_mask)] = True

            # Find all the other indecies that the piece can reach
            while True:
                new_mask = mask.copy()
                for permutation in actions.values():
                    new_mask |= mask[permutation]
                # No new indecies found, break the loop
                if np.all(mask == new_mask):
                    break
                mask = new_mask

            # No orientation found for the piece, cannot remove the indexes
            if np.all(mask == union_mask):
                break

            unorientated_mask = unorientate_mask(mask, cube_size=cube_size)
            union_mask &= ~unorientated_mask
            boolean_mask[unorientated_mask ^ mask] = False

    # 3. Identify piece types that are not in the pattern
    for piece in [Piece.center, Piece.corner, Piece.edge]:
        piece_mask = get_piece_mask(piece, cube_size=cube_size)
        if np.unique(pattern[piece_mask]).size == 1:
            boolean_mask &= ~piece_mask

    idx_set = set(np.where(boolean_mask)[0])
    for permutation in actions.values():
        assert idx_set == set(permutation[boolean_mask]), "Action space and boolean mask mismatch."

    # 4. Reindex the permutations and action space
    actions, pattern = reindex(
        actions=actions,
        pattern=pattern,
        mask=boolean_mask,
    )

    # 5. Split into disjoint action groups and remove bijections
    groups = []
    identity = np.arange(len(pattern))
    all_indecies = set(identity)
    while all_indecies:
        # Initialize a mask for a random idx
        group_mask = np.zeros_like(pattern, dtype=bool)
        group_mask[all_indecies.pop()] = True

        # Find all the other indecies that the piece can reach
        while True:
            new_group_mask = group_mask.copy()
            for permutation in actions.values():
                new_group_mask |= group_mask[permutation]
            # No new indecies found, break the loop
            if np.all(group_mask == new_group_mask):
                break
            group_mask = new_group_mask

        group_idecies = np.where(group_mask)[0]
        all_indecies -= set(group_idecies)
        groups.append(group_idecies)

    # Remove groups that are bijections of each other
    bijective_groups: list[tuple[int, ...]] = []
    for i, group in enumerate(groups):
        added_group = False
        group_mapping = {idx: i for i, idx in enumerate(group)}
        for j, other_group in enumerate(groups[(i + 1) :]):

            # Don't add groups that are already bijective
            already_bijective = False
            for bijective_group in bijective_groups:
                if i in bijective_group and i + 1 + j in bijective_group:
                    already_bijective = True
                    break

            # Don't compare groups of different sizes, they are not injective
            if not len(group) == len(other_group) or already_bijective:
                continue
            group_identity = np.arange(len(group))
            other_group_mapping = {idx: i for i, idx in enumerate(other_group)}
            for permutation in actions.values():
                group_permutation = permutation[group]
                other_group_permutation = permutation[other_group]

                # Map to the new indecies
                group_permutation = np.array([group_mapping[idx] for idx in group_permutation])
                other_group_permutation = np.array(
                    [other_group_mapping[idx] for idx in other_group_permutation]
                )
                if not np.array_equal(
                    group_permutation[invert(other_group_permutation)], group_identity
                ):
                    break
            else:
                insert_idx = -1
                for group_idx, bijective_group in enumerate(bijective_groups):
                    if i in bijective_group:
                        new_bijective_group = (*bijective_group, i + 1 + j)
                        insert_idx = group_idx
                        break
                if insert_idx == -1:
                    bijective_groups.append((i, i + 1 + j))
                else:
                    bijective_groups[insert_idx] = new_bijective_group
                added_group = True
                break
        if not added_group:
            found = False
            for bijective_group in bijective_groups:
                if i in bijective_group:
                    found = True
                    break
            if not found:
                bijective_groups.append((i,))

    # Only keep the first group of each bijective group
    second_boolean_mask = np.zeros_like(pattern, dtype=bool)
    for bijective_group in bijective_groups:
        second_boolean_mask[groups[bijective_group[0]]] = True

    # Update the total boolean mask
    boolean_mask[boolean_mask] = second_boolean_mask

    # 6. Reindex the permutations and action space
    if not np.all(second_boolean_mask):
        actions, pattern = reindex(
            actions=actions,
            pattern=pattern,
            mask=second_boolean_mask,
        )

    return actions, pattern, boolean_mask


def find_rotation_offset(
    permutation: CubePermutation,
    mask: CubeMask | None,
) -> CubePermutation | None:
    """Find the rotational offset between the permutation and the mask.
    It finds the rotation such that perm[not mask] == identity[not mask].

    Args:
        initial_state (CubePermutation): Initial state.
        mask (CubeMask | None, optional): Cube mask.

    Raises:
        ValueError: If the cube size cannot be inferred.

    Returns:
        CubePermutation | None: Offset for the permutation.
    """
    try:
        cube_size = infer_cube_size(permutation)
    except ValueError as exc:
        LOGGER.warning(f"Could not infer cube size: {exc}")
        return None

    if mask is None:
        mask = np.ones_like(permutation, dtype=bool)

    # Naming: XY, X is the up face, Y is the front direction
    standard_rotations = {
        "UF": [],
        "UL": ["y'"],
        "UB": ["y2"],
        "UR": ["y"],
        "FU": ["x", "y2"],
        "FL": ["x", "y'"],
        "FD": ["x"],
        "FR": ["x", "y"],
        "RU": ["z'", "y'"],
        "RF": ["z'"],
        "RD": ["z'", "y"],
        "RB": ["z'", "y2"],
        "BU": ["x'"],
        "BL": ["x'", "y'"],
        "BD": ["x'", "y2"],
        "BR": ["x'", "y"],
        "LU": ["z", "y"],
        "LF": ["z"],
        "LD": ["z", "y'"],
        "LB": ["z", "y2"],
        "DF": ["z2"],
        "DL": ["x2", "y'"],
        "DB": ["x2"],
        "DR": ["x2", "y"],
    }

    for rotation in standard_rotations.values():
        rotated_cube = get_rubiks_cube_state(
            sequence=MoveSequence(rotation),
            cube_size=cube_size,
        )
        if np.array_equal(rotated_cube[~mask], permutation[~mask]):
            return rotated_cube
    return None
