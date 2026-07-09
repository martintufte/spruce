"""IDA* solver."""

from __future__ import annotations

from typing import TYPE_CHECKING

from spruce.solver.ida_star.implementation import ida_star_solver
from spruce.solver.interface import PermutationSolver

if TYPE_CHECKING:
    from spruce.solver.interface import SolverImplementation


class IDAStarSolver(PermutationSolver):
    """Iterative-deepening depth-first search with a pluggable heuristic."""

    @staticmethod
    def _implementation() -> SolverImplementation:
        return ida_star_solver
