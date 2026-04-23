from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from typing import TYPE_CHECKING
from typing import NamedTuple

from rubiks_cube.configuration.enumeration import SearchSide
from rubiks_cube.configuration.enumeration import Status

if TYPE_CHECKING:
    from rubiks_cube.configuration.types import PermutationArray
    from rubiks_cube.move.sequence import MoveSequence


class UnsolveableError(Exception):
    pass


class SearchSummary(NamedTuple):
    solutions: list[MoveSequence]
    walltime: float
    status: Status


class RootedSolution(NamedTuple):
    permutation_index: int
    sequence: MoveSequence


class SearchManySummary(NamedTuple):
    solutions: list[RootedSolution]
    walltime: float
    status: Status


class PermutationSolver(ABC):
    @abstractmethod
    def search(
        self,
        permutations: list[PermutationArray],
        max_solutions_per_permutation: int,
        max_search_depth: int,
        max_time: float,
        side: SearchSide = SearchSide.normal,
    ) -> SearchManySummary: ...
