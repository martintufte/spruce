from __future__ import annotations

import attrs
import numpy as np
import numpy.typing as npt
from bidict import bidict

from rubiks_cube.configuration.types import IndexArray  # noqa: TC001
from rubiks_cube.configuration.types import MaskArray  # noqa: TC001
from rubiks_cube.configuration.types import PatternArray  # noqa: TC001
from rubiks_cube.configuration.types import PermutationArray  # noqa: TC001
from rubiks_cube.representation.pattern import merge_patterns
from rubiks_cube.representation.utils import reindex
from rubiks_cube.transform.interface import SearchProblem
from rubiks_cube.transform.interface import Transform


@attrs.mutable
class FilterRepresentative(Transform):
    representative_identity: PatternArray | None = None
    representative_mask: MaskArray | None = None

    def fit(self, search_problem: SearchProblem) -> SearchProblem:
        indistinguishable = find_indistinguishable_pattern(
            actions=search_problem.actions,
            pattern=search_problem.pattern,
        )
        self.representative_mask = np.zeros_like(indistinguishable, dtype=bool)
        for label in np.unique(indistinguishable):
            self.representative_mask[int(np.where(indistinguishable == label)[0][0])] = True
        self.representative_identity = np.zeros_like(indistinguishable, dtype=int)
        for i, j in enumerate(np.where(self.representative_mask)[0]):
            self.representative_identity[indistinguishable == indistinguishable[j]] = i

        search_problem.actions = {
            key: self.representative_identity[perm][self.representative_mask]
            for key, perm in search_problem.actions.items()
        }
        search_problem.pattern = search_problem.pattern[self.representative_mask]
        return search_problem

    def transform_permutation(self, permutation: PermutationArray) -> PermutationArray:
        assert self.representative_identity is not None
        assert self.representative_mask is not None
        return self.representative_identity[permutation][self.representative_mask]


@attrs.mutable
class FilterAffected(Transform):
    affected_mask: MaskArray | None = None

    def fit(self, search_problem: SearchProblem) -> SearchProblem:
        search_problem.actions, self.affected_mask = filter_affected_space(search_problem.actions)
        search_problem.pattern = search_problem.pattern[self.affected_mask]
        return search_problem

    def transform_permutation(self, permutation: PermutationArray) -> PermutationArray:
        assert self.affected_mask is not None
        return reindex(permutation, self.affected_mask)


@attrs.mutable
class FilterIsomorphic(Transform):
    isomorphic_mask: MaskArray | None = None

    def fit(self, search_problem: SearchProblem) -> SearchProblem:
        search_problem.actions, self.isomorphic_mask = filter_isomorphic_subsets(
            search_problem.actions
        )
        search_problem.pattern = search_problem.pattern[self.isomorphic_mask]
        return search_problem

    def transform_permutation(self, permutation: PermutationArray) -> PermutationArray:
        assert self.isomorphic_mask is not None
        return reindex(permutation, self.isomorphic_mask)


@attrs.mutable
class DisjointSubsetReorderer(Transform):
    subset_sizes: list[int] | None = None
    subset_reorder: PermutationArray | None = None
    subset_reorder_inv: PermutationArray | None = None

    def fit(self, search_problem: SearchProblem) -> SearchProblem:
        (
            search_problem.actions,
            search_problem.pattern,
            self.subset_sizes,
            self.subset_reorder,
            self.subset_reorder_inv,
        ) = reorder_by_disjoint_subsets(search_problem.actions, search_problem.pattern)
        return search_problem

    def transform_permutation(self, permutation: PermutationArray) -> PermutationArray:
        assert self.subset_reorder is not None
        assert self.subset_reorder_inv is not None
        return self.subset_reorder_inv[permutation[self.subset_reorder]]


def find_indistinguishable_pattern(
    actions: dict[str, PermutationArray],
    pattern: PatternArray,
) -> PatternArray:
    """Find indistinguishable pattern from the actions and pattern."""
    indistinguishable: PatternArray = pattern.copy()
    while True:
        new = merge_patterns(
            [indistinguishable, *(indistinguishable[perm] for perm in actions.values())]
        )
        if np.equal(new, indistinguishable).all():
            return indistinguishable
        indistinguishable = new


def filter_affected_space(
    actions: dict[str, PermutationArray],
) -> tuple[dict[str, PermutationArray], MaskArray]:
    """Filter indices that are not affected by the action space."""
    size = next(iter(actions.values())).size

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
    actions: dict[str, PermutationArray],
) -> npt.NDArray[np.int_]:
    """Find disjoint subsets of indices using union-find on the action permutations."""
    size = next(iter(actions.values())).size
    subsets = np.arange(size)
    for permutation in actions.values():
        for i, j in zip(subsets, subsets[permutation], strict=False):
            if i != j:
                subsets[subsets == j] = i
    return subsets


def filter_isomorphic_subsets(
    actions: dict[str, PermutationArray],
) -> tuple[dict[str, PermutationArray], MaskArray]:
    """Remove isomorphic disjoint subsets."""
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
    actions: dict[str, PermutationArray],
    pattern: PatternArray,
) -> tuple[
    dict[str, PermutationArray], PatternArray, list[int], PermutationArray, PermutationArray
]:
    """Reorder indices so that disjoint subsets are contiguous, sorted by subset size."""
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
    subset_idxs: IndexArray,
    other_subset_idxs: IndexArray,
    actions: dict[str, PermutationArray],
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
