from __future__ import annotations

import logging
from functools import lru_cache
from typing import TYPE_CHECKING
from typing import Callable

import numpy as np
import numpy.typing as npt
from bidict import bidict

from rubiks_cube.formatting.regex import canonical_key
from rubiks_cube.representation.mask import combine_masks
from rubiks_cube.representation.mask import get_ones_mask
from rubiks_cube.representation.pattern import get_identity_pattern
from rubiks_cube.representation.pattern import merge_patterns
from rubiks_cube.representation.utils import reindex
from rubiks_cube.solver.branching import compute_branching_factor

if TYPE_CHECKING:
    from rubiks_cube.configuration.types import BoolArray
    from rubiks_cube.configuration.types import CubeMask
    from rubiks_cube.configuration.types import CubePattern
    from rubiks_cube.configuration.types import CubePermutation


LOGGER = logging.getLogger(__name__)


class IndexOptimizer:
    affected_mask: CubeMask
    isomorphic_mask: CubeMask
    mask: CubeMask

    def __init__(self, cube_size: int) -> None:
        """Initialize the index optimizer.

        Args:
            cube_size (int): Size of the cube.
        """
        self.affected_mask = self.isomorphic_mask = self.mask = get_ones_mask(cube_size)

    def fit_transform(
        self,
        actions: dict[str, CubePermutation],
        filter_affected: bool = True,
        filter_isomorphic: bool = True,
    ) -> dict[str, CubePermutation]:
        """Fit the index optimizer to the permutations in the action space."""
        masks = []

        if filter_affected:
            actions, self.affected_mask = filter_affected_space(actions)
            masks.append(self.affected_mask)
            LOGGER.debug(
                f"Filtered not affected ({self.affected_mask.size} -> {sum(self.affected_mask)})"
            )

        if filter_isomorphic:
            actions, self.isomorphic_mask = filter_isomorphic_subsets(actions)
            masks.append(self.isomorphic_mask)
            LOGGER.debug(
                f"Filtered isomorphisms ({sum(self.affected_mask)} -> {sum(self.isomorphic_mask)})"
            )

        self.mask = combine_masks(masks=masks)

        return actions

    def transform_permutation(self, permutation: CubePermutation) -> CubePermutation:
        """Transform the permutation using the mask."""
        return reindex(permutation, self.mask)

    def transform_pattern(self, pattern: CubePattern) -> CubePattern:
        """Transform the pattern using the mask."""
        return pattern[self.mask]


def filter_affected_space(
    actions: dict[str, CubePermutation],
) -> tuple[dict[str, CubePermutation], CubeMask]:
    """Filter indices that are not affected by the action space.

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

    # Set mask as union of all indices that are affected by the actions
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
        for i, j in zip(groups, groups[permutation], strict=False):
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
    """Try creating a consistent bijection between two groups of indices."""
    for other_idx in other_group_idxs:
        bijection_map: bidict[int, int] = bidict({group_idxs[0]: other_idx})
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
                if new_from_idx not in bijection_map:
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


class PatternIndexOptimizer:
    indistinguishable: CubePattern
    representative_mask: CubeMask
    representative_identity: CubePattern

    def __init__(self, cube_size: int) -> None:
        """Initialize the pattern index optimizer.

        Args:
            cube_size (int): Size of the cube.
        """
        self.indistinguishable = get_identity_pattern(cube_size=cube_size)
        self.representative_mask = self.affected_mask = get_ones_mask(cube_size=cube_size)

    def fit_transform(
        self,
        actions: dict[str, CubePermutation],
        pattern: CubePattern,
    ) -> dict[str, CubePermutation]:
        """Fit the pattern optimizer to the cube pattern.

        Args:
            actions (dict[str, CubePermutation]): Action space.
            pattern (CubePattern): Cube pattern.

        Returns:
            CubePattern: Optimized cube pattern.
        """
        self.indistinguishable = find_indistinguishable_pattern(actions, pattern)
        indistinguishable_list = list(self.indistinguishable)

        # Set first occurrence for each indistinguishable subset as representative
        self.representative_mask = np.zeros_like(pattern, dtype=bool)
        unique = np.unique(self.indistinguishable)
        for i in unique:
            self.representative_mask[indistinguishable_list.index(i)] = True

        # Create representative identity permutation
        self.representative_identity = np.zeros_like(self.indistinguishable)
        for i, j in enumerate(np.where(self.representative_mask)[0]):
            self.representative_identity[self.indistinguishable == self.indistinguishable[j]] = i

        # Reindex the actions
        actions = {
            key: self.representative_identity[perm][self.representative_mask]
            for key, perm in actions.items()
        }

        # TODO: This code can potentially be merged with the above code
        # Filter not affected indices
        actions, affected_mask = filter_affected_space(actions)
        self.representative_mask = combine_masks([self.representative_mask, affected_mask])

        # Create representative identity permutation again
        self.representative_identity = np.zeros_like(self.indistinguishable)
        for i, j in enumerate(np.where(self.representative_mask)[0]):
            self.representative_identity[self.indistinguishable == self.indistinguishable[j]] = i

        # Test if a subset of indices are indistinguishable
        LOGGER.debug(f"Filtered indistinguishable ({pattern.size} -> {affected_mask.sum()})")

        return actions

    def transform_permutation(self, permutation: CubePermutation) -> CubePermutation:
        """Transform the permutation using the representative mask."""
        return self.representative_identity[permutation][self.representative_mask]

    def transform_pattern(self, pattern: CubePattern) -> CubePattern:
        """Transform the pattern using the mask."""
        return pattern[self.representative_mask]


def find_indistinguishable_pattern(
    actions: dict[str, CubePermutation],
    pattern: CubePattern,
) -> CubePattern:
    """Find indistinguishable pattern from the actions and pattern.

    Args:
        actions (dict[str, CubePermutation]): Action space.
        pattern (CubePattern): Cube pattern.

    Returns:
        CubePattern: Indistinguishable pattern.
    """

    indistinguishable: CubePattern = pattern.copy()
    while True:
        new = merge_patterns([indistinguishable[perm] for perm in actions.values()])
        if np.equal(new, indistinguishable).all():
            return indistinguishable
        indistinguishable = new


class DtypeOptimizer:
    dtype: type[np.uint8 | np.uint16 | np.uint32] | None = None

    def fit_transform(self, pattern: CubePattern) -> npt.NDArray[np.uint]:
        """Fit and transform the pattern to the optimal data type."""
        n_unique = len(np.unique(pattern))

        if n_unique <= np.iinfo(np.uint8).max:
            self.dtype = np.uint8
        elif n_unique <= np.iinfo(np.uint16).max:
            self.dtype = np.uint16
        else:
            self.dtype = np.uint32

        LOGGER.debug(f"Cast pattern ({n_unique=}) to {self.dtype!s}")

        return pattern.astype(self.dtype)

    def transform_pattern(self, pattern: CubePattern) -> npt.NDArray[np.uint]:
        """Transform the pattern to the optimized data type."""
        if self.dtype is None:
            raise ValueError("The dtype has not been computed yet.")
        return pattern.astype(self.dtype)


class ActionOptimizer:
    key: Callable[[str], tuple[int, ...]] = canonical_key
    adj_matrix: BoolArray | None = None

    def __init__(self, key: Callable[[str], tuple[int, ...]] | None = None) -> None:
        """Initialize the action optimizer.

        Args:
            key (Callable[[str], tuple[int, ...]] | None, optional): Key function for sorting action names.
                Defaults to None.
        """
        self.key = key or canonical_key

    def fit_transform(self, actions: dict[str, CubePermutation]) -> dict[str, CubePermutation]:
        """Set actions in canonical order and build adjacency matrix.

        Args:
            actions (dict[str, CubePermutation]): Action space.

        Returns:
            dict[str, CubePermutation]: Actions sorted in canonical order.
        """
        for permutation in actions.values():
            size = permutation.size
            break

        # Sort the action names based on the key
        actions = {name: actions[name] for name in sorted(actions.keys(), key=self.key)}
        n_actions = len(actions)

        # Create the adjacency matrix
        action_perms = tuple(tuple(perm) for perm in actions.values())
        self.adj_matrix = compute_adjacency_matrix(action_perms, size)

        branching_factor = compute_branching_factor(adj_matrix=self.adj_matrix)
        LOGGER.debug(
            f"Reduced branching factor ({n_actions} ->"
            + f" {round(branching_factor['spectral_radius'], 2)})"
        )

        return actions

    def transform_actions(
        self,
        actions: dict[str, CubePermutation],
    ) -> dict[str, CubePermutation]:
        """Transform actions to the optimized canonical order.

        Args:
            actions (dict[str, CubePermutation]): Action space.

        Returns:
            dict[str, CubePermutation]: Actions sorted in optimized canonical order.
        """
        return {name: actions[name] for name in sorted(actions.keys(), key=self.key)}

    def get_adj_matrix(self) -> BoolArray:
        """Get the adjacency matrix."""
        if self.adj_matrix is None:
            raise ValueError("The adjacency matrix has not been computed yet.")
        return self.adj_matrix


@lru_cache(maxsize=128)
def compute_adjacency_matrix(
    action_perms: tuple[tuple[int, ...], ...],
    size: int,
) -> BoolArray:
    """Compute adjacency matrix for given action permutations.

    Args:
        action_perms (tuple[tuple[int, ...], ...]): Tuple of permutation tuples (for hashability).
        size (int): Size of the permutation space.

    Returns:
        BoolArray: Adjacency matrix as tuple of tuples of bools
    """
    n_actions = len(action_perms)

    # Closed if composition is identity or other permutations
    closed_perms: set[tuple[int, ...]] = {tuple(range(size))}
    closed_perms |= set(action_perms)

    # Build adjacency matrix from canonical order
    adj_matrix = np.ones((n_actions, n_actions), dtype=bool)
    for i, perm_i in enumerate(action_perms):
        perm_i_array = np.array(perm_i)
        for j, perm_j in enumerate(action_perms):
            perm_j_array = np.array(perm_j)
            perm_ji = tuple(perm_j_array[perm_i_array])
            perm_ij = tuple(perm_i_array[perm_j_array])

            # Prune closed permutations and non-canonical commutative order
            if perm_ij in closed_perms or (i > j and perm_ji == perm_ij):
                adj_matrix[i, j] = False
                continue

            # Prune i,j = k,i if k is not i and not a sink action
            for k, perm_k in enumerate(action_perms):
                if k != j and np.sum(adj_matrix[k, :]) > 0:
                    perm_k_array = np.array(perm_k)
                    if perm_ij == tuple(perm_k_array[perm_i_array]):
                        adj_matrix[i, j] = False
                        break

    return adj_matrix
