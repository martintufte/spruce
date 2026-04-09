from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from typing import TYPE_CHECKING

import attrs

if TYPE_CHECKING:
    from typing import Callable

    from rubiks_cube.configuration.types import BoolArray
    from rubiks_cube.configuration.types import PatternArray
    from rubiks_cube.configuration.types import PermutationArray


@attrs.mutable
class SearchProblem:
    actions: dict[str, PermutationArray]
    pattern: PatternArray
    action_sort_key: Callable[[str], tuple[int, ...]] | None = None

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
