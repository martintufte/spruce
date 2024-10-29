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
            verbose (bool): Log debug information.
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


# class MultiTagSolver(Protocol):
#     pass


# class HeuristicSolver(Protocol):
#     ...


# class MetricSolver(Protocol):
#     ...


# class AsyncSolver(Protocol):
#     ...

_ = """
    solver = BidirectionalSolver(
        generator=generator,
        step=step,
        cube_size=cube_size,
        verbose=False,
    )

    # solver.branch_factor
    # solver.optimizer
    # solver.callbacks
    # solver.metrics

    solutions, search_summary = solver.solve(
        sequence=sequence,
        goal_sequence=goal_sequence,
        max_search_depth=max_search_depth,
        n_solutions=n_solutions,
        strategy=strategy,
    )

    # Ideas for search_summary: (SearchSummary class?)
    # search_summary.walltime
    # search_summary.n_solutions
    # search_summary.max_depth
    # search_summary.effective_branch_factor
    # search_summary.effective_depth
    # search_summary.status

    return solutions
"""
