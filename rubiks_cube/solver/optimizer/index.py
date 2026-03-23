from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from typing import Self

import attrs
import numpy as np
import numpy.typing as npt
from bidict import bidict

from rubiks_cube.representation.mask import combine_masks
from rubiks_cube.representation.mask import get_ones_mask
from rubiks_cube.representation.pattern import merge_patterns
from rubiks_cube.representation.permutation import get_identity_permutation
from rubiks_cube.representation.utils import reindex

if TYPE_CHECKING:
    from rubiks_cube.configuration.types import CubeMask
    from rubiks_cube.configuration.types import CubePattern
    from rubiks_cube.configuration.types import CubePermutation


LOGGER = logging.getLogger(__name__)


@attrs.mutable
class IndexOptimizer:
    representative_identity: CubePattern
    representative_mask: CubeMask
    affected_mask: CubeMask
    isomorphic_mask: CubeMask
    mask: CubeMask
    subset_sizes: list[int]
    subset_reorder: CubePermutation
    subset_reorder_inv: CubePermutation

    @classmethod
    def from_cube_size(cls, cube_size: int) -> Self:
        identity = get_identity_permutation(cube_size=cube_size)
        mask = get_ones_mask(cube_size=cube_size)
        return cls(
            representative_identity=identity,
            representative_mask=mask.copy(),
            affected_mask=mask.copy(),
            isomorphic_mask=mask.copy(),
            mask=mask.copy(),
            subset_sizes=[identity.size],
            subset_reorder=identity.copy(),
            subset_reorder_inv=identity.copy(),
        )

    def fit_transform(
        self,
        actions: dict[str, CubePermutation],
        pattern: CubePattern,
        debug: bool = False,
    ) -> tuple[dict[str, CubePermutation], CubePattern]:
        """Fit the optimizer and transform actions and pattern."""

        masks: list[CubeMask] = []

        # Create representative mask and identity
        indistinguishable = find_indistinguishable_pattern(actions, pattern)
        self.representative_mask = np.zeros_like(indistinguishable, dtype=bool)
        for label in np.unique(indistinguishable):
            self.representative_mask[int(np.where(indistinguishable == label)[0][0])] = True
        self.representative_identity = np.zeros_like(indistinguishable, dtype=int)
        for i, j in enumerate(np.where(self.representative_mask)[0]):
            self.representative_identity[indistinguishable == indistinguishable[j]] = i
        actions = {
            key: self.representative_identity[perm][self.representative_mask]
            for key, perm in actions.items()
        }

        # Filter non-affected indices
        actions, self.affected_mask = filter_affected_space(actions)
        masks.append(self.affected_mask)

        # Filter isomorphic subsets
        actions, self.isomorphic_mask = filter_isomorphic_subsets(actions)
        masks.append(self.isomorphic_mask)

        # Combine all masks
        self.mask = combine_masks(masks=masks)
        pattern = pattern[self.representative_mask][self.mask]

        # Reorder indices so disjoint subsets are contiguous, smallest first
        actions, pattern, self.subset_sizes, self.subset_reorder, self.subset_reorder_inv = (
            reorder_by_disjoint_subsets(actions, pattern)
        )

        if debug:
            LOGGER.debug(
                "Filtered indistinguishable, affected and isomporhic "
                f"({self.representative_mask.size} -> {sum(self.representative_mask)} "
                f"-> {sum(self.affected_mask)} -> {sum(self.isomorphic_mask)})"
            )
            LOGGER.debug(f"Disjoint subset sizes: {self.subset_sizes}")

        return actions, pattern

    def transform_permutation(self, permutation: CubePermutation) -> CubePermutation:
        """Transform the permutation to a usable format for actions."""
        # 1. Collapse indistinguishable positions to representatives
        permutation = self.representative_identity[permutation][self.representative_mask]
        # 2. Remove unaffected and isomorphic indices
        permutation = reindex(permutation, self.mask)
        # 3. Conjugate to reordered basis with disjoint subsets are contiguous
        permutation = self.subset_reorder_inv[permutation[self.subset_reorder]]

        return permutation


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
        new = merge_patterns(
            [indistinguishable, *(indistinguishable[perm] for perm in actions.values())]
        )
        if np.equal(new, indistinguishable).all():
            return indistinguishable
        indistinguishable = new


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


def find_disjoint_subsets(
    actions: dict[str, CubePermutation],
) -> npt.NDArray[np.int_]:
    """Find disjoint subsets of indices using union-find on the action permutations.

    Args:
        actions (dict[str, CubePermutation]): Action space.

    Returns:
        npt.NDArray[np.int_]: Subset labels for each index.
    """
    size = next(iter(actions.values())).size
    subsets = np.arange(size)
    for permutation in actions.values():
        for i, j in zip(subsets, subsets[permutation], strict=False):
            if i != j:
                subsets[subsets == j] = i
    return subsets


def filter_isomorphic_subsets(
    actions: dict[str, CubePermutation],
) -> tuple[dict[str, CubePermutation], CubeMask]:
    """Remove isomorphic disjoint subsets.

    Args:
        actions (dict[str, CubePermutation]): Action space.

    Returns:
        tuple[dict[str, CubePermutation], CubeMask]: Filtered action space and isomorphic mask.
    """
    size = next(iter(actions.values())).size
    subset_labels = find_disjoint_subsets(actions)

    # Find isomorphic subsets
    unique_labels = np.unique(subset_labels)
    isomorphisms: list[list[int]] = []

    for i, label in enumerate(unique_labels):
        subset_idxs = np.where(subset_labels == label)[0]
        for other_label in unique_labels[(i + 1) :]:
            other_subset_idxs = np.where(subset_labels == other_label)[0]

            # Skip if sets have different cardinality
            if len(subset_idxs) != len(other_subset_idxs):
                continue

            # Skip if sets are already isomorphic
            for isomorphism in isomorphisms:
                if label in isomorphism and other_label in isomorphism:
                    break
            else:
                if has_consistent_bijection(subset_idxs, other_subset_idxs, actions):
                    for isomorphism in isomorphisms:
                        if label in isomorphism:
                            isomorphism.append(int(other_label))
                            break
                    else:
                        isomorphisms.append([int(label), int(other_label)])

    # Remove isomorphisms
    isomorphic_mask = np.ones(size, dtype=bool)
    for isomorphism in isomorphisms:
        for label in isomorphism[1:]:
            isomorphic_mask[subset_labels == label] = False

    # Reindex the actions
    actions = {key: reindex(perm, isomorphic_mask) for key, perm in actions.items()}

    return actions, isomorphic_mask


def reorder_by_disjoint_subsets(
    actions: dict[str, CubePermutation],
    pattern: CubePattern,
) -> tuple[dict[str, CubePermutation], CubePattern, list[int], CubePermutation, CubePermutation]:
    """Reorder indices so that disjoint subsets are contiguous, sorted by subset size.

    Subsets of indices that don't influence each other through any action are
    identified via union-find. The indices are then permuted so that the smallest
    subset comes first, then the next smallest, etc.

    Args:
        actions: Action space.
        pattern: Cube pattern.

    Returns:
        Reordered actions, reordered pattern, subset sizes, reorder and reorder_inv permutations.
    """
    size = next(iter(actions.values())).size
    subset_labels = find_disjoint_subsets(actions)

    # Collect subsets and sort by size (smallest first)
    unique_labels = np.unique(subset_labels)
    subsets = [np.where(subset_labels == label)[0] for label in unique_labels]
    subsets.sort(key=len)

    subset_sizes = [len(s) for s in subsets]

    # Build the reordering: reorder[new_idx] = old_idx
    reorder = np.concatenate(subsets).astype(np.uint)

    # Build the inverse mapping: reorder_inv[old_idx] = new_idx
    reorder_inv = np.empty(size, dtype=np.uint)
    reorder_inv[reorder] = np.arange(size, dtype=np.uint)

    # Reorder actions by conjugation: new_action = reorder_inv[action[reorder]]
    actions = {key: reorder_inv[perm[reorder]] for key, perm in actions.items()}

    # Reorder pattern
    pattern = pattern[reorder]

    return actions, pattern, subset_sizes, reorder, reorder_inv


def has_consistent_bijection(
    subset_idxs: npt.NDArray[np.int_],
    other_subset_idxs: npt.NDArray[np.int_],
    actions: dict[str, CubePermutation],
) -> bool:
    """Try creating a consistent bijection between two groups of indices."""
    for other_idx in other_subset_idxs:
        bijection_map: bidict[int, int] = bidict({subset_idxs[0]: other_idx})
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
