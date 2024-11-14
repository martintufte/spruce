from typing import Protocol

from rubiks_cube.configuration.types import CubePattern
from rubiks_cube.configuration.types import CubePermutation
from rubiks_cube.solver.search import SearchSummary


class UnsolveableError(Exception):
    pass


class MaxDepthReachedError(Exception):
    pass


class PatternSolver(Protocol):
    @property
    def branch_factor(self) -> int:
        """Branch factor of the solver."""
        ...

    def compile(
        self,
        actions: dict[str, CubePermutation],
        pattern: CubePattern,
        verbose: bool = False,
    ) -> None:
        """
        Compile the solver for a given actions and step.

        Args:
            actions (dict[str, CubePermutation]): Actions with permutations.
            pattern (CubePattern): Cube pattern to solve.
            verbose (bool): Log debug information.

        """
        ...

    def solve(
        self,
        permutation: CubePermutation,
        n_solutions: int = 1,
        min_search_depth: int = 0,
        max_search_depth: int = 10,
    ) -> tuple[list[list[str]], SearchSummary]:
        """Solve the pattern. Raise an exception if it is unsolveable or max depth is reached."""
        ...


# TODO: Solving multiple patterns at once
# class MultiPatternSolver(Protocol):
#     pass


# TODO: Solving with heuristics
# class HeuristicSolver(Protocol):
#     ...


# TODO: Solving with metrics
# class MetricSolver(Protocol):
#     ...
