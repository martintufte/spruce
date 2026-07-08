from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from typing import TYPE_CHECKING
from typing import NamedTuple

from spruce.configuration.enumeration import SearchSide
from spruce.configuration.enumeration import Status

if TYPE_CHECKING:
    from spruce.move.sequence import MoveSequence
    from spruce.types import PermutationArray


class SearchSummary[SolutionT](NamedTuple):
    solutions: list[SolutionT]
    walltime: float
    status: Status


class RootedSolution(NamedTuple):
    permutation_index: int
    sequence: MoveSequence


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
