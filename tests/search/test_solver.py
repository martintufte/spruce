from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any

import numpy as np
import pytest

from spruce.algebra import get_permutation
from spruce.autotagger.pattern import get_patterns
from spruce.move.sequence import MoveSequence
from spruce.move.sequence import sequence_from_word
from spruce.puzzle.cube.goals import Goal
from spruce.puzzle.cube.group import build_move_meta
from spruce.puzzle.cube.group import default_generator
from spruce.puzzle.cube.spec import Puzzle
from spruce.puzzle.cube.variants import Variant
from spruce.search import solve_patterns
from spruce.search.bidirectional import BidirectionalSolver
from spruce.search.enumeration import SearchSide
from spruce.search.enumeration import Status

if TYPE_CHECKING:
    from collections.abc import Set as AbstractSet

    from spruce.algebra.meta import MoveMeta
    from spruce.search.interface import LabelledSolution
    from spruce.search.interface import SearchSummary
    from spruce.types import MoveSymbol


def solve_goal(
    scramble: MoveSequence,
    *,
    move_meta: MoveMeta,
    generator: AbstractSet[MoveSymbol],
    goal: Goal,
    variants: list[Variant] | None = None,
    **options: Any,
) -> tuple[SearchSummary[LabelledSolution], list[MoveSequence]]:
    """Resolve a goal into labelled patterns and assemble sequences, as an app would.

    `solve_patterns` knows nothing about goals, variants or notation, so this mirrors the
    glue in the application layer to keep these tests expressed in cube terms.
    """
    pattern = get_patterns(puzzle=Puzzle._3x3x3)[goal]
    patterns = {variant.value: pattern[variant] for variant in (variants or list(pattern.variants))}

    summary = solve_patterns(
        get_permutation(sequence=scramble, move_meta=move_meta),
        actions=move_meta.get_actions(generator=generator),
        patterns=patterns,
        validator=pattern.validator,
        validator_key=goal.value if pattern.validator is not None else None,
        **options,
    )
    sequences = [
        sequence_from_word(solution.word, on_inverse=solution.side is SearchSide.inverse)
        for solution in summary.solutions
    ]

    return summary, sequences


def test_main() -> None:
    """Example of solving a step with a generator on a 3x3 cube."""
    move_meta = build_move_meta(puzzle=Puzzle._3x3x3)

    search_summary, solutions = solve_goal(
        MoveSequence.from_str("M2 U M U2 M' U M2"),
        move_meta=move_meta,
        generator=move_meta.to_symbols("M", "U"),
        goal=Goal.solved,
        max_search_depth=8,
        max_solutions=1,
        search_side=SearchSide.normal,
    )

    assert isinstance(solutions, list)
    assert len(solutions) == 1
    assert search_summary.walltime > 0
    assert search_summary.status is Status.success

    # The label of the pattern that was matched is echoed back on the solution
    assert search_summary.solutions[0].label == Variant.none.value
    assert search_summary.solutions[0].side is SearchSide.normal


def test_default() -> None:
    """Example of solving a step with a generator on a 3x3 cube."""
    puzzle = Puzzle._3x3x3
    move_meta = build_move_meta(puzzle=puzzle)

    scrambles = [
        MoveSequence.from_str("L"),
        MoveSequence.from_str("R"),
        MoveSequence.from_str("U"),
        MoveSequence.from_str("D"),
        MoveSequence.from_str("F"),
        MoveSequence.from_str("B"),
    ]
    generator = default_generator(puzzle)

    for scramble in scrambles:
        search_summary, solutions = solve_goal(
            scramble,
            move_meta=move_meta,
            generator=generator,
            goal=Goal.solved,
            max_search_depth=10,
            max_solutions=2,
            search_side=SearchSide.normal,
        )
        assert len(solutions) == 2
        assert isinstance(solutions, list)
        assert search_summary.walltime > 0
        assert search_summary.status is Status.success

        # First solution has length == 1
        assert len(solutions[0]) == 1
        # Second solution is distinct from the first
        assert len(solutions[1]) > 1


def test_search_inverse() -> None:
    puzzle = Puzzle._3x3x3
    move_meta = build_move_meta(puzzle=puzzle)

    search_summary, solutions = solve_goal(
        MoveSequence.from_str("R"),
        move_meta=move_meta,
        generator=default_generator(puzzle),
        goal=Goal.solved,
        max_search_depth=10,
        max_solutions=1,
        search_side=SearchSide.inverse,
    )

    assert search_summary.status is Status.success
    assert len(solutions) == 1
    assert len(solutions[0]) == 1
    assert len(solutions[0].inverse) > 0
    assert search_summary.solutions[0].side is SearchSide.inverse


def test_solve_patterns_rejects_empty_patterns() -> None:
    move_meta = build_move_meta(puzzle=Puzzle._3x3x3)

    with pytest.raises(ValueError, match="No patterns to solve"):
        solve_patterns(
            get_permutation(sequence=MoveSequence.from_str("R"), move_meta=move_meta),
            actions=move_meta.get_actions(generator=move_meta.to_symbols("R")),
            patterns={},
        )


def test_bidirectional_solver_search_returns_rooted_solutions() -> None:
    move_meta = build_move_meta(puzzle=Puzzle._3x3x3)

    actions = move_meta.get_actions(generator=move_meta.to_symbols("R"))
    pattern = np.arange(54, dtype=np.uint8)
    solver = BidirectionalSolver.from_actions_and_pattern(
        actions=actions,
        pattern=pattern,
        optimize_indices=False,
    )
    permutations = [
        get_permutation(sequence=MoveSequence.from_str("R"), move_meta=move_meta),
        get_permutation(sequence=MoveSequence.from_str("R'"), move_meta=move_meta),
    ]

    summary = solver.search(
        permutations=permutations,
        max_solutions_per_permutation=1,
        max_search_depth=1,
        max_time=10.0,
        side=SearchSide.normal,
    )

    assert summary.status is Status.success
    assert len(summary.solutions) == 2
    by_root = {
        solution.permutation_index: str(
            sequence_from_word(
                solution.word,
                on_inverse=solution.side is SearchSide.inverse,
            ),
        )
        for solution in summary.solutions
    }
    assert by_root[0] == "R'"
    assert by_root[1] == "R"


@pytest.mark.xfail(
    strict=True,
    reason=(
        "EO inverse solutions currently include equivalent front/back terminal variants, "
        "e.g. (F B), (F' B), (F B') and (F' B')."
    ),
)
def test_eo_inverse_deduplicates_terminal_front_back_variants() -> None:
    puzzle = Puzzle._3x3x3
    move_meta = build_move_meta(puzzle=puzzle)

    _summary, solutions = solve_goal(
        MoveSequence.from_str(
            "R' U' F L2 U B' L2 D2 F2 L D2 B2 L2 R2 D2 U' L' D R B' F' D R' U' F",
        ),
        move_meta=move_meta,
        generator=default_generator(puzzle),
        goal=Goal.eo,
        variants=[Variant.fb],
        max_search_depth=6,
        max_solutions=200,
        search_side=SearchSide.inverse,
    )

    sequences = {str(solution) for solution in solutions}
    assert "(F B)" in sequences
    assert "(F' B)" not in sequences
    assert "(F B')" not in sequences
    assert "(F' B')" not in sequences
