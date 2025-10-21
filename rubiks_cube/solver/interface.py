from typing import Protocol

from rubiks_cube.configuration.enumeration import Status
from rubiks_cube.configuration.types import CubePattern
from rubiks_cube.configuration.types import CubePermutation


class UnsolveableError(Exception):
    pass


class SearchSummary:
    walltime: float
    n_solutions: int
    max_search_depth: int
    status: Status

    def __init__(
        self,
        walltime: float,
        n_solutions: int,
        max_search_depth: int,
        status: Status,
    ) -> None:
        """Initialize the SearchSummary class.

        Args:
            walltime (float): Walltime.
            n_solutions (int): Number of solutions.
            max_search_depth (int): Maximum search depth.
            status (Status): Status of the search.
        """
        self.walltime = walltime
        self.n_solutions = n_solutions
        self.max_search_depth = max_search_depth
        self.status = status


class PatternSolver(Protocol):
    @property
    def branch_factor(self) -> int:
        """Compute effective branching factor of the solver."""
        ...

    def compile(
        self,
        actions: dict[str, CubePermutation],
        pattern: CubePattern,
    ) -> None:
        """Compile the solver for a given actions and step.

        Args:
            actions (dict[str, CubePermutation]): Actions with permutations.
            pattern (CubePattern): Cube pattern to solve.
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
