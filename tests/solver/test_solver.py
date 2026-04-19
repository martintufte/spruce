from __future__ import annotations

import numpy as np

from rubiks_cube.configuration import DEFAULT_GENERATOR_MAP
from rubiks_cube.configuration.enumeration import Goal
from rubiks_cube.configuration.enumeration import SearchSide
from rubiks_cube.configuration.enumeration import SolveStrategy
from rubiks_cube.configuration.enumeration import Status
from rubiks_cube.move.generator import MoveGenerator
from rubiks_cube.move.meta import MoveMeta
from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.representation import get_rubiks_cube_permutation
from rubiks_cube.solver import solve_pattern
from rubiks_cube.solver.actions import get_actions
from rubiks_cube.solver.bidirectional import BidirectionalSolver


def test_main() -> None:
    """Example of solving a step with a generator on a 3x3 cube."""
    move_meta = MoveMeta.from_cube_size(3)

    sequence = MoveSequence.from_str("M2 U M U2 M' U M2")
    generator = MoveGenerator.from_str("<M, U>")

    search_summary = solve_pattern(
        sequence=sequence,
        move_meta=move_meta,
        generator=generator,
        algorithms=None,
        goal=Goal.solved,
        max_search_depth=8,
        max_solutions=1,
        solve_strategy=SolveStrategy.normal,
    )
    solutions = search_summary.solutions

    assert isinstance(solutions, list)
    assert len(solutions) == 1
    assert search_summary.walltime > 0
    assert search_summary.status is Status.Success


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
    generator = MoveGenerator.from_str(DEFAULT_GENERATOR_MAP[3])

    for scramble in scrambles:
        search_summary = solve_pattern(
            sequence=scramble,
            move_meta=move_meta,
            generator=generator,
            algorithms=None,
            goal=Goal.solved,
            max_search_depth=10,
            max_solutions=2,
            solve_strategy=SolveStrategy.normal,
        )
        solutions = search_summary.solutions
        assert len(solutions) == 2
        assert isinstance(solutions, list)
        assert search_summary.walltime > 0
        assert search_summary.status is Status.Success

        # First solution has length == 1
        assert len(solutions[0]) == 1
        # Second solution is distinct from the first
        assert len(solutions[1]) > 1


def test_search_inverse() -> None:
    scramble = MoveSequence.from_str("R")
    generator = MoveGenerator.from_str(DEFAULT_GENERATOR_MAP[3])
    move_meta = MoveMeta.from_cube_size(3)

    search_summary = solve_pattern(
        sequence=scramble,
        move_meta=move_meta,
        generator=generator,
        algorithms=None,
        goal=Goal.solved,
        max_search_depth=10,
        max_solutions=1,
        solve_strategy=SolveStrategy.inverse,
    )

    assert search_summary.status is Status.Success
    assert len(search_summary.solutions) == 1
    assert len(search_summary.solutions[0]) == 1
    assert len(search_summary.solutions[0].inverse) > 0


def test_bidirectional_solver_search_returns_rooted_solutions() -> None:
    move_meta = MoveMeta.from_cube_size(3)

    actions = get_actions(move_meta=move_meta, generator=MoveGenerator.from_str("<R>"))
    pattern = np.arange(54, dtype=np.uint8)
    solver = BidirectionalSolver.from_actions_and_pattern(
        actions=actions,
        pattern=pattern,
        validator=None,
        optimize_indices=False,
    )
    permutations = [
        get_rubiks_cube_permutation(sequence=MoveSequence.from_str("R"), move_meta=move_meta),
        get_rubiks_cube_permutation(sequence=MoveSequence.from_str("R'"), move_meta=move_meta),
    ]

    summary = solver.search(
        permutations=permutations,
        max_solutions_per_permutation=1,
        min_search_depth=0,
        max_search_depth=1,
        max_time=10.0,
        side=SearchSide.normal,
    )

    assert summary.status is Status.Success
    assert len(summary.solutions) == 2
    by_root = {solution.permutation_index: str(solution.sequence) for solution in summary.solutions}
    assert by_root[0] == "R'"
    assert by_root[1] == "R"
