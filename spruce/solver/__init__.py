from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from spruce.solver.bidirectional import BidirectionalSolver
from spruce.solver.enumeration import SearchSide
from spruce.solver.enumeration import Status
from spruce.solver.interface import LabelledSolution
from spruce.solver.interface import SearchSummary

if TYPE_CHECKING:
    from collections.abc import Mapping

    from spruce.types import MoveSymbol
    from spruce.types import PatternArray
    from spruce.types import PermutationArray
    from spruce.types import PermutationValidator

LOGGER = logging.getLogger(__name__)


def solve_patterns(
    permutation: PermutationArray,
    *,
    actions: dict[MoveSymbol, PermutationArray],
    patterns: Mapping[str, PatternArray],
    validator: PermutationValidator | None = None,
    validator_key: str | None = None,
    max_search_depth: int = 10,
    max_solutions: int = 1,
    search_side: SearchSide = SearchSide.normal,
    max_time: float = 60.0,
) -> SearchSummary[LabelledSolution]:
    """Search for the shortest words taking the permutation to any of the patterns.

    Each pattern is an independent target: the search succeeds as soon as the permutation
    matches any one of them, and the returned solutions are pooled, deduplicated and
    ranked by length across all of them. A pattern labels the indices of the permutation,
    so a pattern may leave indices indistinguishable from each other, which is what lets
    partial targets (orientations, permutations of a subset of the pieces) be expressed.

    For every pattern the actions and the pattern are first compiled into a reduced search
    problem: redundant actions are pruned, indices that are bijections of each other or
    that always stay solved are collapsed, and the permutations are cast to the narrowest
    dtype that can index them. The compiled problem is then searched from both the initial
    permutation and the pattern simultaneously, meeting in the middle.

    Args:
        permutation (PermutationArray): Permutation to solve.
        actions (dict[MoveSymbol, PermutationArray]): Action space, keyed by symbol.
        patterns (Mapping[str, PatternArray]): Target patterns, keyed by a caller-chosen
            label that is echoed back on each solution.
        validator (PermutationValidator | None, optional): Extra predicate a candidate
            permutation must satisfy to count as solved. Defaults to None.
        validator_key (str | None, optional): Name of `validator`, carried so the compiled
            solver can be serialized. Defaults to None.
        max_search_depth (int, optional): Maximum search depth. Defaults to 10.
        max_solutions (int, optional): Maximum number of solutions. Defaults to 1.
        search_side (SearchSide, optional): Search strategy (normal, inverse, both).
            Defaults to SearchSide.normal.
        max_time (float, optional): Maximum time in seconds, shared across all patterns
            and sides. Defaults to 60.0.

    Raises:
        ValueError: If no patterns are given.

    Returns:
        SearchSummary[LabelledSolution]: Summary of the search.
    """
    if not patterns:
        raise ValueError("No patterns to solve.")

    LOGGER.info(
        "Solving %s pattern(s) with strategy '%s'..",
        len(patterns),
        search_side.value,
    )

    if search_side is SearchSide.both:
        search_sides = [SearchSide.normal, SearchSide.inverse]
    else:
        search_sides = [search_side]

    all_solutions: list[LabelledSolution] = []
    status = Status.failure
    total_walltime = 0.0

    for label, pattern in patterns.items():
        solver = BidirectionalSolver.from_actions_and_pattern(
            actions=actions,
            pattern=pattern,
            validator=validator,
            validator_key=validator_key,
            optimize_indices=validator is None,
            debug=True,
        )

        for side in search_sides:
            remaining_time = max_time - total_walltime
            if remaining_time <= 0:
                break

            pattern_summary = solver.search(
                permutations=[permutation],
                max_solutions_per_permutation=max_solutions,
                max_search_depth=max_search_depth,
                max_time=remaining_time,
                side=side,
            )

            total_walltime += pattern_summary.walltime
            if pattern_summary.status is Status.failure:
                continue

            status = Status.success
            all_solutions.extend(
                LabelledSolution(label=label, word=solution.word, side=solution.side)
                for solution in pattern_summary.solutions
            )

    unique_solutions = {
        (solution.side, tuple(solution.word)): solution for solution in all_solutions
    }
    solutions = sorted(
        unique_solutions.values(),
        key=lambda solution: (len(solution.word), solution.side.value, tuple(solution.word)),
    )[:max_solutions]

    LOGGER.info("Solver found %s solutions in %.3fs", len(solutions), total_walltime)

    return SearchSummary(
        solutions=solutions,
        walltime=total_walltime,
        status=status,
    )
