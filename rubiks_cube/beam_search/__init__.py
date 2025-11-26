from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from typing import Literal
from typing import TypeAlias

from rubiks_cube.configuration.enumeration import Status
from rubiks_cube.solver.interface import SearchSummary

if TYPE_CHECKING:
    from rubiks_cube.move.sequence import MoveSequence

LOGGER = logging.getLogger(__name__)


SearchStrategy: TypeAlias = Literal["always", "never", "before"]


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
