from __future__ import annotations

import logging
from functools import lru_cache
from typing import TYPE_CHECKING
from typing import Callable
from typing import Self

import attrs
import numpy as np

from rubiks_cube.configuration.regex import canonical_key
from rubiks_cube.solver.branching import compute_branching_factor

if TYPE_CHECKING:
    from rubiks_cube.configuration.types import BoolArray
    from rubiks_cube.configuration.types import CubePermutation


LOGGER = logging.getLogger(__name__)


@attrs.mutable
class ActionOptimizer:
    adj_matrix: BoolArray | None
    key: Callable[[str], tuple[int, ...]]

    @classmethod
    def from_key(cls, key: Callable[[str], tuple[int, ...]] | None = None) -> Self:
        """Initialize the action optimizer from a key.

        Args:
            key (Callable[[str], tuple[int, ...]] | None, optional): Key function for sorting
                actions. Defaults to None.
        """
        if key is None:
            key = canonical_key
        return cls(adj_matrix=None, key=key)

    def fit_transform(
        self,
        actions: dict[str, CubePermutation],
        debug: bool = False,
    ) -> dict[str, CubePermutation]:
        """Put actions in canonical order and build adjacency matrix.

        Args:
            actions (dict[str, CubePermutation]): Action space.
            debug (bool, optional): Whether to log debug statements. Defaults to False.

        Returns:
            dict[str, CubePermutation]: Actions sorted in canonical order.
        """
        if len(actions) == 0:
            raise ValueError("Action space is empty.")

        # Sort the action names based on the key
        actions = {name: actions[name] for name in sorted(actions.keys(), key=self.key)}
        first_permutation = next(iter(actions.values()))
        size = np.asarray(first_permutation).size

        # Create the adjacency matrix
        action_perms = tuple(tuple(perm) for perm in actions.values())
        self.adj_matrix = compute_adjacency_matrix(action_perms, size)

        if debug:
            n_actions = len(actions)
            branching_factor = compute_branching_factor(adj_matrix=self.adj_matrix)
            LOGGER.debug(
                f"Reduced branching factor ({n_actions} ->"
                + f" {round(branching_factor['spectral_radius'], 2)})"
            )

        return actions

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
