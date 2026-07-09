"""Bidirectional solver."""

from __future__ import annotations

from typing import TYPE_CHECKING

from spruce.solver.bidirectional.implementation import bidirectional_solver
from spruce.solver.interface import PermutationSolver

if TYPE_CHECKING:
    from spruce.solver.interface import SolverImplementation


class BidirectionalSolver(PermutationSolver):
    """Breadth-first search from both the scramble and the goal, meeting in the middle."""

    @staticmethod
    def _implementation() -> SolverImplementation:
        return bidirectional_solver
