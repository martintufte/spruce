from __future__ import annotations

import logging
from abc import ABC
from abc import abstractmethod
from typing import TYPE_CHECKING
from typing import Literal
from typing import TypeAlias

from rubiks_cube.configuration.enumeration import Status
from rubiks_cube.solver.bidirectional.beta import bidirectional_solver
from rubiks_cube.solver.interface import SearchSummary

if TYPE_CHECKING:
    from rubiks_cube.configuration.types import BoolArray
    from rubiks_cube.configuration.types import CubePattern
    from rubiks_cube.configuration.types import CubePermutation
    from rubiks_cube.move.sequence import MoveSequence
    from rubiks_cube.solver.optimizers import IndexOptimizer

LOGGER = logging.getLogger(__name__)


SearchStrategy: TypeAlias = Literal["always", "never", "before"]


# TODO: How to chain the solving steps together?
class SolveStep(ABC):
    @abstractmethod
    def solve(
        self,
        permutation: CubePermutation,
        n_solutions: int,
        max_time: float,
    ) -> list[list[str]] | None: ...


class BidirectionalSolveStep(SolveStep):
    min_search_depth: int
    max_search_depth: int
    search_strategy: SearchStrategy
    pattern: CubePattern
    actions: dict[str, CubePermutation]
    adj_matrix: BoolArray
    index_optimizer: IndexOptimizer

    def solve(
        self,
        permutation: CubePermutation,
        n_solutions: int,
        max_time: float,
    ) -> list[list[str]] | None:
        initial_permutation = self.index_optimizer.transform_permutation(permutation)

        return bidirectional_solver(
            initial_permutation=initial_permutation,
            actions=self.actions,
            pattern=self.pattern,
            max_search_depth=self.max_search_depth,
            n_solutions=n_solutions,
            adj_matrix=self.adj_matrix,
            max_time=max_time,
        )


def beam_search(
    sequence: MoveSequence,
    beam_width: int,
    n_solutions: int = 1,
    max_time: float = 60.0,
) -> SearchSummary:
    """Solve the Rubik's cube with a beam search strategy.

    Args:
        sequence (MoveSequence): Sequence to scramble the cube.
        beam_width (int): The maximum number of candidates to keep at each step.
        goal (Goal | None, optional): Goal to solve. Defaults to Goal.Solved.
        n_solutions (int, optional): Number of solutions to return. Defaults to 1.
        max_time (float, optional): Maximum time in seconds. Defaults to 60.0.

    Returns:
        SearchSummary: Search summary.
    """
    LOGGER.info("Starting beam search..")

    return SearchSummary(
        solutions=[],
        walltime=0.0,
        status=Status.Failure,
    )
