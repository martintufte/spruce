from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Self

import attrs

from spruce.search.transform.action import ActionOptimizer
from spruce.search.transform.cast import CastDtype
from spruce.search.transform.fused_index import FusedIndexTransform
from spruce.search.transform.index import DisjointSubsetReorderer
from spruce.search.transform.index import FilterAffected
from spruce.search.transform.index import FilterIsomorphic
from spruce.search.transform.index import FilterRepresentative
from spruce.search.transform.interface import IndexTransform
from spruce.search.transform.interface import Transform
from spruce.types import PermutationArray  # noqa: TC001

if TYPE_CHECKING:
    from spruce.search.transform.interface import SearchProblem


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

    def fuse(self) -> Self:
        """Return a new Pipeline where every contiguous block of IndexTransforms is
        replaced by a single FusedIndexTransform. All other transforms are kept as-is."""
        new_transforms: list[Transform] = []
        ts = self.transforms
        i = 0
        while i < len(ts):
            j = i
            while j < len(ts) and isinstance(ts[j], IndexTransform):
                j += 1
            if j > i:
                block = [t for t in ts[i:j] if isinstance(t, IndexTransform)]
                new_transforms.append(FusedIndexTransform.from_index_transforms(block))
                i = j
            else:
                new_transforms.append(ts[i])
                i += 1
        return type(self)(transforms=new_transforms)


def create_transform_pipeline(
    optimize_indices: bool,
    debug: bool = False,
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
            ],
        )

    transforms.append(CastDtype())
    transforms.append(ActionOptimizer(debug=debug))

    return Pipeline(transforms=transforms)
