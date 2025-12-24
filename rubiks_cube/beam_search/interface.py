from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rubiks_cube.solver.interface import PermutationSolver


class BeamSolver:
    solvers: list[PermutationSolver]
