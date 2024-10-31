from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import numpy as np
import numpy.typing as npt
from bidict import bidict

from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.solver.solver_abc import UnsolveableError
from rubiks_cube.state import get_rubiks_cube_state
from rubiks_cube.state.mask import combine_masks
from rubiks_cube.state.mask import get_ones_mask
from rubiks_cube.state.utils import infer_cube_size
from rubiks_cube.state.utils import invert
from rubiks_cube.state.utils import reindex

if TYPE_CHECKING:
    from rubiks_cube.configuration.types import CubeMask
    from rubiks_cube.configuration.types import CubePattern
    from rubiks_cube.configuration.types import CubePermutation


LOGGER = logging.getLogger(__name__)


class IndexOptimizer:
    cube_size: int
    affected_mask: CubeMask
    isomorphic_mask: CubeMask
    mask: CubeMask

    def __init__(self, cube_size: int) -> None:
        self.cube_size = cube_size
        self.affected_mask = self.isomorphic_mask = self.mask = get_ones_mask(cube_size)

    def fit_transform(
        self,
        actions: dict[str, CubePermutation],
        filter_affected: bool = True,
        filter_isomorphic: bool = True,
    ) -> dict[str, CubePermutation]:
        """Fit the index optimizer to the permutations in the action space and cube pattern."""
        applied_masks = []

        if filter_affected:
            actions, self.affected_mask = filter_affected_space(actions)
            applied_masks.append(self.affected_mask)
            LOGGER.info(
                f"Filtered not affected ({len(self.affected_mask)} -> {sum(self.affected_mask)})"
            )

        if filter_isomorphic:
            actions, self.isomorphic_mask = filter_isomorphic_subsets(actions)
            applied_masks.append(self.isomorphic_mask)
            LOGGER.info(
                f"Filtered isomorphisms ({sum(self.affected_mask)} -> {sum(self.isomorphic_mask)})"
            )

        self.mask = combine_masks(applied_masks)

        return actions

    def transform_permutation(self, permutation: CubePermutation) -> CubePermutation:
        """Transform the permutation using the mask."""

        offset = find_rotation_offset(permutation, self.affected_mask)
        if offset is not None:
            inv_offset = invert(offset)
            return reindex(inv_offset[permutation], self.mask)

        raise UnsolveableError("Could not transform the cube, unsolveable.")

    def transform_pattern(self, pattern: CubePattern) -> CubePattern:
        """Transform the pattern using the mask."""
        return pattern[self.mask]


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


def filter_affected_space(
    actions: dict[str, CubePermutation],
) -> tuple[dict[str, CubePermutation], CubeMask]:
    """Filter indecies that are not affected by the action space.

    Args:
        actions (dict[str, CubePermutation]): Action space.

    Returns:
        tuple[dict[str, CubePermutation], CubeMask]: Filtered action space and affected mask.
    """
    for permutation in actions.values():
        size = permutation.size
        break

    # Set the mask and identity action
    affected_mask = np.zeros(size, dtype=bool)
    identity = np.arange(size)

    # Set mask as union of all indecies that are affected by the actions
    for permutation in actions.values():
        affected_mask |= identity != permutation

    # Reindex the actions
    actions = {key: reindex(perm, affected_mask) for key, perm in actions.items()}

    return actions, affected_mask


def filter_isomorphic_subsets(
    actions: dict[str, CubePermutation],
) -> tuple[dict[str, CubePermutation], CubeMask]:
    """Remove isomorphic disjoint subsets.

    Args:
        actions (dict[str, CubePermutation]): Action space.

    Returns:
        tuple[dict[str, CubePermutation], CubeMask]: Filtered action space and isomorphic mask.
    """
    for permutation in actions.values():
        size = permutation.size
        break

    # Find disjoint subsets
    groups = np.arange(size)
    for permutation in actions.values():
        for i, j in zip(groups, groups[permutation]):
            if i != j:
                groups[groups == j] = i

    # Find isomorphic subgroups
    unique_groups = np.unique(groups)
    isomorphisms: list[list[int]] = []

    for i, idx in enumerate(unique_groups):
        group_idxs = np.where(groups == idx)[0]
        for other_idx in unique_groups[(i + 1) :]:
            other_group_idxs = np.where(groups == other_idx)[0]

            # Skip if sets have different cardinality
            if len(group_idxs) != len(other_group_idxs):
                continue

            # Skip if sets are already isomorphic
            for isomorphism in isomorphisms:
                if idx in isomorphism and other_idx in isomorphism:
                    break
            else:
                if has_consistent_bijection(group_idxs, other_group_idxs, actions):
                    for isomorphism in isomorphisms:
                        if idx in isomorphism:
                            isomorphism.append(int(other_idx))
                            break
                    else:
                        isomorphisms.append([int(idx), int(other_idx)])

    # Remove isomorphisms
    isomorphic_mask = np.ones(size, dtype=bool)
    for isomorphism in isomorphisms:
        for idx in isomorphism[1:]:
            isomorphic_mask[groups == idx] = False

    # Reindex the actions
    actions = {key: reindex(perm, isomorphic_mask) for key, perm in actions.items()}

    return actions, isomorphic_mask


def has_consistent_bijection(
    group_idxs: npt.NDArray[np.int_],
    other_group_idxs: npt.NDArray[np.int_],
    actions: dict[str, CubePermutation],
) -> bool:
    """Try creating a consistent bijection between two groups of indecies."""
    for to_idx in other_group_idxs:
        bijection_map: bidict[int, int] = bidict({group_idxs[0]: to_idx})
        consistent = True

        # Check that bijection is consistent for all actions
        for permutation in actions.values():
            if not consistent:
                break

            # Collect changes to the bijection here
            new_bijection_map: bidict[int, int] = bidict()

            for from_idx, to_idx in bijection_map.items():
                new_from_idx = permutation[from_idx]
                new_to_idx = permutation[to_idx]

                # Add new bijections if not seen
                if new_from_idx not in bijection_map.keys():
                    if new_to_idx in bijection_map.values():
                        consistent = False
                        break
                    new_bijection_map[new_from_idx] = new_to_idx

                # Check if the bijection is consistent
                elif bijection_map[new_from_idx] != new_to_idx:
                    consistent = False
                    break

            # Update bijection with new mappings if consistent
            if consistent:
                bijection_map.update(new_bijection_map)
            else:
                break

        if consistent:
            return True

    return False
