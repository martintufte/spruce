from __future__ import annotations

import numpy as np
import pytest

from spruce.configuration import DEFAULT_GENERATOR_MAP
from spruce.configuration.enumeration import Goal
from spruce.configuration.enumeration import SearchSide
from spruce.configuration.enumeration import Status
from spruce.configuration.enumeration import Variant
from spruce.move.generator import MoveGenerator
from spruce.move.meta import MoveMeta
from spruce.move.sequence import MoveSequence
from spruce.representation import get_rubiks_cube_permutation
from spruce.solver import solve_pattern
from spruce.solver.bidirectional import BidirectionalSolver


def test_main() -> None:
    """Example of solving a step with a generator on a 3x3 cube."""
    move_meta = MoveMeta.from_cube_size(3)

    sequence = MoveSequence.from_str("M2 U M U2 M' U M2")
    generator = MoveGenerator.from_str("<M, U>")

    search_summary = solve_pattern(
        sequence=sequence,
        move_meta=move_meta,
        generator=generator,
        goal=Goal.solved,
        max_search_depth=8,
        max_solutions=1,
        search_side=SearchSide.normal,
    )
    solutions = search_summary.solutions

    assert isinstance(solutions, list)
    assert len(solutions) == 1
    assert search_summary.walltime > 0
    assert search_summary.status is Status.success


def test_default() -> None:
    """Example of solving a step with a generator on a 3x3 cube."""
    move_meta = MoveMeta.from_cube_size(3)

    scrambles = [
        MoveSequence.from_str("L"),
        MoveSequence.from_str("R"),
        MoveSequence.from_str("U"),
        MoveSequence.from_str("D"),
        MoveSequence.from_str("F"),
        MoveSequence.from_str("B"),
    ]
    generator = MoveGenerator.from_str(DEFAULT_GENERATOR_MAP[54])

    for scramble in scrambles:
        search_summary = solve_pattern(
            sequence=scramble,
            move_meta=move_meta,
            generator=generator,
            goal=Goal.solved,
            max_search_depth=10,
            max_solutions=2,
            search_side=SearchSide.normal,
        )
        solutions = search_summary.solutions
        assert len(solutions) == 2
        assert isinstance(solutions, list)
        assert search_summary.walltime > 0
        assert search_summary.status is Status.success

        # First solution has length == 1
        assert len(solutions[0]) == 1
        # Second solution is distinct from the first
        assert len(solutions[1]) > 1


def test_search_inverse() -> None:
    scramble = MoveSequence.from_str("R")
    generator = MoveGenerator.from_str(DEFAULT_GENERATOR_MAP[54])
    move_meta = MoveMeta.from_cube_size(3)

    search_summary = solve_pattern(
        sequence=scramble,
        move_meta=move_meta,
        generator=generator,
        goal=Goal.solved,
        max_search_depth=10,
        max_solutions=1,
        search_side=SearchSide.inverse,
    )

    assert search_summary.status is Status.success
    assert len(search_summary.solutions) == 1
    assert len(search_summary.solutions[0]) == 1
    assert len(search_summary.solutions[0].inverse) > 0


def test_bidirectional_solver_search_returns_rooted_solutions() -> None:
    move_meta = MoveMeta.from_cube_size(3)

    actions = move_meta.get_actions(generator=MoveGenerator.from_str("<R>"))
    pattern = np.arange(54, dtype=np.uint8)
    solver = BidirectionalSolver.from_actions_and_pattern(
        actions=actions,
        pattern=pattern,
        optimize_indices=False,
    )
    permutations = [
        get_rubiks_cube_permutation(sequence=MoveSequence.from_str("R"), move_meta=move_meta),
        get_rubiks_cube_permutation(sequence=MoveSequence.from_str("R'"), move_meta=move_meta),
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
    by_root = {solution.permutation_index: str(solution.sequence) for solution in summary.solutions}
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
    move_meta = MoveMeta.from_cube_size(3)
    generator = MoveGenerator.from_str(DEFAULT_GENERATOR_MAP[54])
    scramble = MoveSequence.from_str(
        "R' U' F L2 U B' L2 D2 F2 L D2 B2 L2 R2 D2 U' L' D R B' F' D R' U' F",
    )

    summary = solve_pattern(
        sequence=scramble,
        move_meta=move_meta,
        generator=generator,
        goal=Goal.eo,
        variants=[Variant.fb],
        max_search_depth=6,
        max_solutions=200,
        search_side=SearchSide.inverse,
    )

    assert summary.status is Status.success
    sequences = {str(solution) for solution in summary.solutions}
    assert "(F B)" in sequences
    assert "(F' B)" not in sequences
    assert "(F B')" not in sequences
    assert "(F' B')" not in sequences
