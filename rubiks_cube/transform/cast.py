from __future__ import annotations

from typing import TYPE_CHECKING

import attrs
import numpy as np

from rubiks_cube.transform.interface import SearchProblem
from rubiks_cube.transform.interface import Transform

if TYPE_CHECKING:
    from rubiks_cube.configuration.types import PermutationArray


def get_index_dtype(size: int) -> np.dtype[np.unsignedinteger]:
    """Get the smallest unsigned integer dtype that can index its elements."""
    if size <= np.iinfo(np.uint8).max + 1:
        return np.dtype(np.uint8)
    if size <= np.iinfo(np.uint16).max + 1:
        return np.dtype(np.uint16)
    return np.dtype(np.uint32)


@attrs.mutable
class CastDtype(Transform):
    permutation_dtype: np.dtype[np.unsignedinteger] | None = None

    def fit(self, search_problem: SearchProblem) -> SearchProblem:
        if len(search_problem.actions) == 0:
            raise ValueError("Action space is empty.")

        size = next(iter(search_problem.actions.values())).size
        self.permutation_dtype = get_index_dtype(size=size)

        search_problem.pattern = search_problem.pattern.astype(np.uint8)
        search_problem.actions = {
            key: perm.astype(self.permutation_dtype, copy=False)
            for key, perm in search_problem.actions.items()
        }
        return search_problem

    def transform_permutation(self, permutation: PermutationArray) -> PermutationArray:
        if self.permutation_dtype is None:
            raise ValueError("CastDtype must be fitted before transforming permutations.")
        return permutation.astype(self.permutation_dtype, copy=False)
