from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Self

import attrs

from rubiks_cube.configuration.types import PermutationArray  # noqa: TC001
from rubiks_cube.transform.interface import IndexTransform
from rubiks_cube.transform.interface import SearchProblem
from rubiks_cube.transform.interface import Transform

if TYPE_CHECKING:
    from collections.abc import Sequence


@attrs.mutable
class FusedIndexTransform(Transform):
    """Inference-only replacement for a block of IndexTransforms.

    Built by ``Pipeline.fuse``; not fitted directly.
    At inference time the transform reduces to a single operation:
        output = fused_forward[permutation[fused_select]]
    """

    fused_select: PermutationArray | None = None
    fused_forward: PermutationArray | None = None

    def fit(self, search_problem: SearchProblem) -> SearchProblem:
        raise NotImplementedError("FusedIndexTransform cannot be fitted; use Pipeline.fuse().")

    def transform_permutation(self, permutation: PermutationArray) -> PermutationArray:
        assert self.fused_select is not None
        assert self.fused_forward is not None
        return self.fused_forward[permutation[self.fused_select]]

    @classmethod
    def from_index_transforms(cls, transforms: Sequence[IndexTransform]) -> Self:
        """Compose a sequence of fitted IndexTransforms into a single fused transform.

        Each transform contributes a (select, forward) pair. Composition:
            fused_select = s_0[s_1[...[s_n]...]]
            fused_forward = f_n[...[f_1[f_0]]]
        so that output = fused_forward[perm[fused_select]] is equivalent to
        applying every transform in sequence.
        """
        fused_select, fused_forward = transforms[0].index_parts()
        for t in transforms[1:]:
            s, f = t.index_parts()
            fused_select = fused_select[s]
            fused_forward = f[fused_forward]
        return cls(fused_select=fused_select, fused_forward=fused_forward)
