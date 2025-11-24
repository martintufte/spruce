from __future__ import annotations

from typing import TYPE_CHECKING

from rubiks_cube.configuration.enumeration import Status
from rubiks_cube.solver.interface import SearchSummary
from rubiks_cube.solver.interface import Solver

if TYPE_CHECKING:
    from rubiks_cube.move.sequence import MoveSequence


class BiDirectionalSolver(Solver):
    def solve(self, sequence: MoveSequence) -> SearchSummary:
        return SearchSummary(
            solutions=[],
            walltime=0.0,
            status=Status.Failure,
        )
