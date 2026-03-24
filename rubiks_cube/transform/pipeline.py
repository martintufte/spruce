from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Callable

import attrs

from rubiks_cube.configuration.regex import canonical_key
from rubiks_cube.transform.action import ActionOptimizer
from rubiks_cube.transform.cast import CastDtype
from rubiks_cube.transform.index import DisjointSubsetReorderer
from rubiks_cube.transform.index import FilterAffected
from rubiks_cube.transform.index import FilterIsomorphic
from rubiks_cube.transform.index import FilterRepresentative
from rubiks_cube.transform.interface import Transform

if TYPE_CHECKING:
    from rubiks_cube.configuration.types import PermutationArray
    from rubiks_cube.transform.interface import SearchProblem


@attrs.mutable
class Pipeline(Transform):
    transforms: list[Transform]

    def fit(self, search_problem: SearchProblem) -> SearchProblem:
        for transform in self.transforms:
            search_problem = transform.fit(search_problem)
        return search_problem

    def transform_permutation(self, permutation: PermutationArray) -> PermutationArray:
        for transform in self.transforms:
            permutation = transform.transform_permutation(permutation)
        return permutation


def create_transform_pipeline(
    optimize_indices: bool,
    debug: bool = False,
    key: Callable[[str], tuple[int, ...]] | None = None,
) -> Pipeline:
    """Create a pipeline given the settings."""
    transforms: list[Transform] = []

    if optimize_indices:
        transforms.extend(
            [
                FilterRepresentative(),
                FilterAffected(),
                FilterIsomorphic(),
                DisjointSubsetReorderer(),
            ]
        )

    transforms.append(CastDtype())

    if key is None:
        key = canonical_key

    action_optimizer = ActionOptimizer.from_key(key=key, debug=debug)
    transforms.append(action_optimizer)

    return Pipeline(transforms=transforms)
