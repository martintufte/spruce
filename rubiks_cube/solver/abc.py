from typing import Protocol

from rubiks_cube.move.generator import MoveGenerator
from rubiks_cube.move.sequence import MoveSequence


class UnsolveableError(Exception):
    pass


class MaxDepthReachedError(Exception):
    pass


class StepSolver(Protocol):
    @property
    def branch_factor(self) -> int:
        """Branch factor of the solver."""
        ...

    def compile(
        self,
        generator: MoveGenerator,
        step: str,
        cube_size: int,
        verbose: bool = False,
    ) -> None:
        """Compile the solver for a given actions and step.

        Args:
            generator (MoveGenerator): Move generator.
            step (str): Step to solve.
            cube_size (int): Size of the cube.
            optimizers (list[str]): Optimizers to use.
            verbose (bool): Print debug information.
        """
        ...

    def solve(
        self,
        sequence: MoveSequence,
        goal_sequence: MoveSequence | None = None,
        n_solutions: int = 1,
        min_depth: int = 0,
        max_depth: int = 10,
    ) -> list[MoveSequence]:
        """Solve the step. Raise an exception if it is unsolveable or max depth is reached."""
        ...


# class MultiStepSolver(Protocol):
#     pass


# class HeuristicSolver(Protocol):
#     ...


# class MetricSolver(Protocol):
#     ...


# class OnnxExportSolver(Protocol):
#     ...


# class AsyncSolver(Protocol):
#     ...


# class OffsetSolver(Protocol):
#     ...
