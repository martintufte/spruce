"""Unidirectional brute-force solver."""

from __future__ import annotations

from typing import TYPE_CHECKING

from spruce.solver.interface import PermutationSolver
from spruce.solver.unidirectional.implementation import unidirectional_solver

if TYPE_CHECKING:
    from spruce.solver.interface import SolverImplementation


class UnidirectionalSolver(PermutationSolver):
    """Breadth-first search from the scramble only, checking states against the goal."""

    @staticmethod
    def _implementation() -> SolverImplementation:
        return unidirectional_solver
