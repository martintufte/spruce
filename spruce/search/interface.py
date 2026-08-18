from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from typing import TYPE_CHECKING
from typing import NamedTuple

from spruce.search.enumeration import SearchSide
from spruce.search.enumeration import Status

if TYPE_CHECKING:
    from spruce.types import MoveSymbol
    from spruce.types import PermutationArray


class SearchSummary[SolutionT](NamedTuple):
    solutions: list[SolutionT]
    walltime: float
    status: Status


class RootedSolution(NamedTuple):
    """A word solving one of the searched permutations, and the side it applies to."""

    permutation_index: int
    word: list[MoveSymbol]
    side: SearchSide


class LabelledSolution(NamedTuple):
    """A word solving one of the searched patterns, and the side it applies to."""

    label: str
    word: list[MoveSymbol]
    side: SearchSide


class PermutationSolver(ABC):
    @abstractmethod
    def search(
        self,
        permutations: list[PermutationArray],
        max_solutions_per_permutation: int,
        max_search_depth: int,
        max_time: float,
        side: SearchSide = SearchSide.normal,
    ) -> SearchSummary[RootedSolution]: ...
