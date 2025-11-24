from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from typing import TYPE_CHECKING
from typing import NamedTuple

if TYPE_CHECKING:
    from rubiks_cube.configuration.enumeration import Status
    from rubiks_cube.move.sequence import MoveSequence


class UnsolveableError(Exception):
    pass


class SearchSummary(NamedTuple):
    solutions: list[MoveSequence]
    walltime: float
    status: Status


class Solver(ABC):
    @abstractmethod
    def solve(self, sequence: MoveSequence) -> SearchSummary: ...
