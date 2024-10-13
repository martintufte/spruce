from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import numpy as np

from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.state import get_rubiks_cube_state
from rubiks_cube.state.utils import infer_cube_size
from rubiks_cube.state.utils import invert
from rubiks_cube.state.utils import reindex

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
        actions, self.mask = optimize_actions(actions)
        pattern = pattern[self.mask]

        return actions, pattern

    def transform(self, perm: CubePermutation) -> CubePermutation:
        """Transform the permutation using the mask.

        Args:
            perm (CubePermutation): Initial permutation.

        Returns:
            CubePermutation: Transformed permutation.
        """
        assert self.mask is not None
        return reindex(perm, self.mask)


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


def optimize_actions(
    actions: dict[str, CubePermutation],
) -> tuple[dict[str, CubePermutation], CubeMask]:
    """Reduce the complexity of the action space.

    1. Add indecies that are not affected by the action space.
    2. Split into disjoint action groups and remove bijections

    Args:
        actions (dict[str, CubePermutation]): Action space.

    Returns:
        tuple[dict[str, CubePermutation], CubeState]: Optimized
            action space and pattern that can be used equivalently by the solver.
    """
    lengths = [permutation.size for permutation in actions.values()]
    assert len(set(lengths)) == 1, "All permutations must have the same length!"

    length = lengths[0]
    first_mask = np.zeros(length, dtype=bool)
    first_identity = np.arange(length)

    # 1. Add indexes that are affected by the actions
    for permutation in actions.values():
        first_mask |= first_identity != permutation
    actions = {key: reindex(perm, first_mask) for key, perm in actions.items()}

    # 2. Split into disjoint action groups and remove bijections
    groups = []
    second_length = sum(first_mask)

    all_indecies = set(range(second_length))
    while all_indecies:
        # Initialize a mask for the first available idx
        group_mask = np.zeros(second_length, dtype=bool)
        group_mask[all_indecies.pop()] = True

        # Find all the other indecies that the idx can reach with the action space
        while True:
            new_group_mask = group_mask.copy()
            for permutation in actions.values():
                new_group_mask |= group_mask[permutation]

            if np.all(group_mask == new_group_mask):
                break
            group_mask = new_group_mask

        group_indecies = np.where(group_mask)[0]
        all_indecies -= set(group_indecies)
        groups.append(group_indecies)

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
    second_mask = np.zeros(second_length, dtype=bool)
    for bijective_group in bijective_groups:
        second_mask[groups[bijective_group[0]]] = True

    # Update the total boolean mask
    first_mask[first_mask] = second_mask
    actions = {key: reindex(perm, second_mask) for key, perm in actions.items()}

    return actions, first_mask
