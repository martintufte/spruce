from __future__ import annotations

from abc import ABC
from abc import abstractmethod

import attrs

from spruce.types import BoolArray  # noqa: TC001
from spruce.types import PatternArray  # noqa: TC001
from spruce.types import PermutationArray  # noqa: TC001


@attrs.mutable
class SearchProblem:
    actions: dict[str, PermutationArray]
    pattern: PatternArray

    # Artifacts from fitting the search problem
    adj_matrix: BoolArray | None = None


@attrs.mutable
class Transform(ABC):

    @abstractmethod
    def fit(self, search_problem: SearchProblem) -> SearchProblem:
        """Fit self to the state."""

    @abstractmethod
    def transform_permutation(self, permutation: PermutationArray) -> PermutationArray:
        """Transform the permutation."""


@attrs.mutable
class IndexTransform(Transform):
    @abstractmethod
    def index_parts(self) -> tuple[PermutationArray, PermutationArray]:
        """Return (select, forward) for this transform.

        ``select`` has shape ``(n_out,)`` mapping each output position back to its
        source position in the input space. ``forward`` has shape ``(n_in,)`` mapping
        each input value to its corresponding output value.
        """
