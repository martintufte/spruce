from __future__ import annotations

import logging
from functools import lru_cache
from typing import TYPE_CHECKING

import attrs
import numpy as np

from rubiks_cube.configuration.regex import canonical_key
from rubiks_cube.configuration.types import BoolArray  # noqa: TC001
from rubiks_cube.transform.interface import SearchProblem
from rubiks_cube.transform.interface import Transform

if TYPE_CHECKING:
    from rubiks_cube.configuration.types import PermutationArray


LOGGER = logging.getLogger(__name__)


@lru_cache(maxsize=128)
def compute_adjacency_matrix(
    action_perms: tuple[tuple[int, ...], ...],
    size: int,
) -> BoolArray:
    """Compute adjacency matrix for given action permutations."""
    n_actions = len(action_perms)

    # Closed if composition is identity or other permutations
    closed_perms: set[tuple[int, ...]] = {tuple(range(size))}
    closed_perms |= set(action_perms)

    # Build adjacency matrix from canonical order
    adj_matrix = np.ones((n_actions, n_actions), dtype=bool)
    for i, perm_i in enumerate(action_perms):
        perm_i_array = np.asarray(perm_i, dtype=np.int32)
        for j, perm_j in enumerate(action_perms):
            perm_j_array = np.asarray(perm_j, dtype=np.int32)
            perm_ji = tuple(perm_j_array[perm_i_array])
            perm_ij = tuple(perm_i_array[perm_j_array])

            # Prune closed permutations and non-canonical commutative order
            if perm_ij in closed_perms or (i > j and perm_ji == perm_ij):
                adj_matrix[i, j] = False
                continue

            # Prune i,j = k,i if k is not i and not a sink action
            for k, perm_k in enumerate(action_perms):
                if k != j and np.sum(adj_matrix[k, :]) > 0:
                    perm_k_array = np.asarray(perm_k, dtype=np.int32)
                    if perm_ij == tuple(perm_k_array[perm_i_array]):
                        adj_matrix[i, j] = False
                        break

    return adj_matrix


@attrs.mutable
class ActionOptimizer(Transform):
    adj_matrix: BoolArray | None = None
    action_names: list[str] | None = None
    debug: bool = False

    def fit(self, search_problem: SearchProblem) -> SearchProblem:
        """Put actions in canonical order and build adjacency matrix."""
        actions = search_problem.actions
        if len(actions) == 0:
            raise ValueError("Action space is empty.")

        key = (
            search_problem.action_sort_key
            if search_problem.action_sort_key is not None
            else canonical_key
        )

        # Sort the action names based on the key and record the rank
        actions = {name: actions[name] for name in sorted(actions.keys(), key=key)}
        self.action_names = list(actions.keys())
        first_permutation = next(iter(actions.values()))
        size = np.asarray(first_permutation).size

        # Create the adjacency matrix
        action_perms = tuple(tuple(perm) for perm in actions.values())
        self.adj_matrix = compute_adjacency_matrix(action_perms, size)

        if self.debug:
            from rubiks_cube.solver.branching import compute_branching_factor  # noqa: PLC0415

            n_actions = len(actions)
            branching_factor = compute_branching_factor(adj_matrix=self.adj_matrix)
            LOGGER.debug(
                "Reduced branching factor (%s -> %s)",
                n_actions,
                round(branching_factor["spectral_radius"], 2),
            )

        search_problem.actions = actions
        search_problem.adj_matrix = self.adj_matrix
        return search_problem

    def fit_transform(
        self,
        actions: dict[str, PermutationArray],
        debug: bool | None = None,
    ) -> dict[str, PermutationArray]:
        """Backward-compatible fit+transform helper."""
        if debug is not None:
            self.debug = debug
        search_problem = SearchProblem(actions=actions, pattern=np.zeros(0, dtype=np.uint))
        return self.fit(search_problem).actions

    def transform_permutation(self, permutation: PermutationArray) -> PermutationArray:
        """Actions-only optimization does not alter state permutations."""
        return permutation

    def get_adj_matrix(self) -> BoolArray:
        """Get the adjacency matrix."""
        if self.adj_matrix is None:
            raise ValueError("The adjacency matrix has not been computed yet.")
        return self.adj_matrix
