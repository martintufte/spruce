from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from typing import Any

import numpy as np
from bidict import bidict

from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.state import get_rubiks_cube_state
from rubiks_cube.state.utils import infer_cube_size
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


def has_consistent_bijection(
    group_idxs: np.ndarray[Any, Any],
    other_group_idxs: np.ndarray[Any, Any],
    actions: dict[str, CubePermutation],
) -> bool:
    """Try creating a consistent bijection between two groups of indecies."""
    for to_idx in other_group_idxs:
        bijection: bidict[int, int] = bidict({group_idxs[0]: to_idx})
        consistent = True

        # Check that bijection is consistent for all actions
        for permutation in actions.values():
            if not consistent:
                break

            # Collect changes to the bijection here
            new_bijections: bidict[int, int] = bidict()

            for from_idx, to_idx in bijection.items():
                new_from_idx = permutation[from_idx]
                new_to_idx = permutation[to_idx]

                # Add new bijections if not seen
                if new_from_idx not in bijection.keys():
                    if new_to_idx in bijection.values():
                        consistent = False
                        break
                    new_bijections[new_from_idx] = new_to_idx

                # Check if the bijection is consistent
                elif bijection[new_from_idx] != new_to_idx:
                    consistent = False
                    break

            # If bijection was consistent, update with new bijections
            if consistent:
                bijection.update(new_bijections)
            else:
                break

        # Found a consistent bijection
        if consistent:
            return True

    return False


def optimize_actions(
    actions: dict[str, CubePermutation],
) -> tuple[dict[str, CubePermutation], CubeMask]:
    """Reduce the complexity of the action space.

    1. Only use indecies that are not affected by the action space.
    2. Remove isomorphic subgroups.

    Args:
        actions (dict[str, CubePermutation]): Action space.

    Returns:
        tuple[dict[str, CubePermutation], CubeState]: Optimized
            action space and pattern that can be used equivalently by the solver.
    """
    lengths = set(permutation.size for permutation in actions.values())
    assert len(lengths) == 1, "All permutations must have the same length!"

    # 1. Remove the set of indecies that are not affected by the action space

    # Set the mask and identity action
    length = lengths.pop()
    mask = np.zeros(length, dtype=bool)
    identity = np.arange(length)

    # Set mask as union of all indecies that are affected by the actions
    for permutation in actions.values():
        mask |= identity != permutation
    actions = {key: reindex(permutation, mask) for key, permutation in actions.items()}

    # 2. Remove isomorphic subgroups

    # Find disjoint groups
    second_length = sum(mask)
    groups = np.arange(second_length)
    for permutation in actions.values():
        for i, j in zip(groups, permutation):
            if i != j:
                groups[groups == j] = i

    # Find isomorphic groups
    unique_groups = np.unique(groups)
    isomorphisms: list[list[int]] = []

    for i, idx in enumerate(unique_groups):
        group_idxs = np.where(groups == idx)[0]
        for other_idx in unique_groups[(i + 1) :]:
            other_group_idxs = np.where(groups == other_idx)[0]

            # Skip if groups have different cardinality
            if len(group_idxs) != len(other_group_idxs):
                continue

            # Skip if groups are already isomorphic
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
    second_mask = np.ones(second_length, dtype=bool)
    for isomorphism in isomorphisms:
        for idx in isomorphism[1:]:
            second_mask[groups == idx] = False

    # Update mask and reindex the actions
    mask[mask] = second_mask
    actions = {key: reindex(permutation, second_mask) for key, permutation in actions.items()}

    # 3. Sort the groups
    # sort_permutation = [x[0] for x in sorted(enumerate(groups[second_mask]), key=lambda x: x[1])]

    return actions, mask


def test_alg() -> None:
    from rubiks_cube.move.algorithm import MoveAlgorithm
    from rubiks_cube.solver.actions import get_action_space

    alg = MoveAlgorithm("Ua-perm", "M2 U M U2 M' U M2")
    alg = MoveAlgorithm("A-perm", "R' F R' B2 R F' R' B2 R2")
    actions = get_action_space(algorithms=[alg], cube_size=4)

    actions, mask = optimize_actions(actions)
    print(actions)


def test_gen() -> None:
    from rubiks_cube.move.generator import MoveGenerator
    from rubiks_cube.solver.actions import get_action_space

    gen = MoveGenerator("<U, M>")
    actions = get_action_space(generator=gen, cube_size=3)

    actions, mask = optimize_actions(actions)
    print(actions)
    print("Reduced the space from:", len(mask), "to", sum(mask), "indecies.")

    new_actions, new_mask = optimize_actions(actions)
    assert sum(mask) == sum(new_mask)


if __name__ == "__main__":
    # test_alg()
    test_gen()
