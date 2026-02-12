from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from typing import TYPE_CHECKING
from typing import NamedTuple

from rubiks_cube.configuration.enumeration import Status

if TYPE_CHECKING:
    from rubiks_cube.configuration.enumeration import Status
    from rubiks_cube.configuration.types import CubePermutation
    from rubiks_cube.move.sequence import MoveSequence


class UnsolveableError(Exception):
    pass


class SearchSummary(NamedTuple):
    solutions: list[MoveSequence]
    walltime: float
    status: Status


class PermutationSolver(ABC):
    @abstractmethod
    def search(
        self,
        permutation: CubePermutation,
        max_solutions: int,
        max_time: float,
    ) -> list[list[str]] | None: ...
