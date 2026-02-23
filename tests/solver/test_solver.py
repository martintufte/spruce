from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from rubiks_cube.configuration import DEFAULT_GENERATOR
from rubiks_cube.configuration.enumeration import Goal
from rubiks_cube.configuration.enumeration import SearchSide
from rubiks_cube.configuration.enumeration import SolveStrategy
from rubiks_cube.configuration.enumeration import Status
from rubiks_cube.move.generator import MoveGenerator
from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.move.utils import is_niss
from rubiks_cube.representation import get_rubiks_cube_permutation
from rubiks_cube.solver import solve_pattern
from rubiks_cube.solver.actions import get_actions
from rubiks_cube.solver.bidirectional import BidirectionalSolver
from rubiks_cube.solver.interface import SearchSummary

if TYPE_CHECKING:
    import pytest


def test_main() -> None:
    """Example of solving a step with a generator on a 3x3 cube."""
    cube_size = 3
    sequence = MoveSequence.from_str("M2 U M U2 M' U M2")
    generator = MoveGenerator.from_str("<M, U>")

    search_summary = solve_pattern(
        sequence=sequence,
        generator=generator,
        goal=Goal.solved,
        max_search_depth=8,
        max_solutions=1,
        solve_strategy=SolveStrategy.normal,
        cube_size=cube_size,
    )
    solutions = search_summary.solutions

    assert isinstance(solutions, list)
    assert len(solutions) == 1
    assert search_summary.walltime > 0
    assert search_summary.status is Status.Success


def test_default() -> None:
    """Example of solving a step with a generator on a 3x3 cube."""
    cube_size = 3
    scrambles = [
        MoveSequence.from_str("L"),
        MoveSequence.from_str("R"),
        MoveSequence.from_str("U"),
        MoveSequence.from_str("D"),
        MoveSequence.from_str("F"),
        MoveSequence.from_str("B"),
    ]
    generator = MoveGenerator.from_str(DEFAULT_GENERATOR)

    for scramble in scrambles:
        search_summary = solve_pattern(
            sequence=scramble,
            generator=generator,
            goal=Goal.solved,
            max_search_depth=10,
            max_solutions=2,
            solve_strategy=SolveStrategy.normal,
            cube_size=cube_size,
        )
        solutions = search_summary.solutions
        assert len(solutions) == 2
        assert isinstance(solutions, list)
        assert search_summary.walltime > 0
        assert search_summary.status is Status.Success

        # First solution has length == 1
        assert len(solutions[0]) == 1
        # Second solution has length == 8
        assert len(solutions[1]) == 8


def test_search_inverse() -> None:
    cube_size = 3
    scramble = MoveSequence.from_str("R")
    generator = MoveGenerator.from_str(DEFAULT_GENERATOR)

    search_summary = solve_pattern(
        sequence=scramble,
        generator=generator,
        goal=Goal.solved,
        max_search_depth=10,
        max_solutions=1,
        solve_strategy=SolveStrategy.inverse,
        cube_size=cube_size,
    )

    assert search_summary.status is Status.Success
    assert len(search_summary.solutions) == 1
    assert len(search_summary.solutions[0]) == 1
    assert is_niss(search_summary.solutions[0][0])


def test_solve_strategy_both_merges_and_deduplicates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeSolver:
        def search(
            self,
            permutation: np.ndarray,
            max_solutions: int,
            min_search_depth: int,
            max_search_depth: int,
            max_time: float,
            side: SearchSide = SearchSide.normal,
        ) -> SearchSummary:
            del permutation, max_solutions, min_search_depth, max_search_depth, max_time
            if side is SearchSide.inverse:
                return SearchSummary(
                    solutions=[
                        MoveSequence.from_str("(R)"),
                        MoveSequence.from_str("U"),
                    ],
                    walltime=0.2,
                    status=Status.Success,
                )
            return SearchSummary(
                solutions=[
                    MoveSequence.from_str("U"),
                    MoveSequence.from_str("R"),
                ],
                walltime=0.1,
                status=Status.Success,
            )

    monkeypatch.setattr(
        "rubiks_cube.solver.get_actions",
        lambda generator, algorithms, cube_size: {},
    )
    monkeypatch.setattr(
        "rubiks_cube.solver.get_matchable_patterns",
        lambda goal, cube_size: ["p1"],
    )
    monkeypatch.setattr(
        "rubiks_cube.solver.get_rubiks_cube_permutation",
        lambda sequence, initial_permutation=None, cube_size=3, invert_after=False: np.array(
            [0],
            dtype=np.uint8,
        ),
    )
    monkeypatch.setattr(
        "rubiks_cube.solver.BidirectionalSolver.from_actions_and_pattern",
        lambda actions, pattern, cube_size, optimize_indices, solution_validator: FakeSolver(),
    )

    search_summary = solve_pattern(
        sequence=MoveSequence(),
        generator=MoveGenerator.from_str("<U>"),
        goal=Goal.solved,
        max_solutions=2,
        solve_strategy=SolveStrategy.both,
        cube_size=3,
    )

    assert search_summary.status is Status.Success
    assert np.isclose(search_summary.walltime, 0.3)
    assert search_summary.solutions == [
        MoveSequence.from_str("(R)"),
        MoveSequence.from_str("R"),
    ]


def test_solve_pattern_aggregates_multi_pattern_summaries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Search summary should aggregate across all matched goal patterns."""

    class FakeSolver:
        def __init__(self, pattern: object) -> None:
            self.pattern = pattern

        def search(
            self,
            permutation: np.ndarray,
            max_solutions: int,
            min_search_depth: int,
            max_search_depth: int,
            max_time: float,
            side: SearchSide = SearchSide.normal,
        ) -> SearchSummary:
            del permutation, max_solutions, min_search_depth, max_search_depth, max_time
            del side
            if self.pattern == "p1":
                return SearchSummary(
                    solutions=[MoveSequence.from_str("R")],
                    walltime=0.2,
                    status=Status.Success,
                )
            return SearchSummary(
                solutions=[],
                walltime=0.3,
                status=Status.Failure,
            )

    monkeypatch.setattr(
        "rubiks_cube.solver.get_actions",
        lambda generator, algorithms, cube_size: {},
    )
    monkeypatch.setattr(
        "rubiks_cube.solver.get_matchable_patterns",
        lambda goal, cube_size: ["p1", "p2"],
    )
    monkeypatch.setattr(
        "rubiks_cube.solver.get_rubiks_cube_permutation",
        lambda sequence, initial_permutation=None, cube_size=3, invert_after=False: np.array(
            [0],
            dtype=np.uint8,
        ),
    )
    monkeypatch.setattr(
        "rubiks_cube.solver.BidirectionalSolver.from_actions_and_pattern",
        lambda actions, pattern, cube_size, optimize_indices, solution_validator: FakeSolver(
            pattern=pattern
        ),
    )

    search_summary = solve_pattern(
        sequence=MoveSequence(),
        generator=MoveGenerator.from_str("<U>"),
        goal=Goal.solved,
        max_solutions=1,
        cube_size=3,
    )

    assert search_summary.status is Status.Success
    assert search_summary.solutions == [MoveSequence.from_str("R")]
    assert search_summary.walltime == 0.5


def test_bidirectional_solver_search_many_returns_rooted_solutions() -> None:
    actions = get_actions(generator=MoveGenerator.from_str("<R>"), cube_size=3)
    pattern = np.arange(54, dtype=np.uint8)
    solver = BidirectionalSolver.from_actions_and_pattern(
        actions=actions,
        pattern=pattern,
        cube_size=3,
        optimize_indices=False,
        solution_validator=None,
    )
    permutations = [
        get_rubiks_cube_permutation(sequence=MoveSequence.from_str("R"), cube_size=3),
        get_rubiks_cube_permutation(sequence=MoveSequence.from_str("R'"), cube_size=3),
    ]

    summary = solver.search_many(
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


if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.WARNING)
    LOGGER = logging.getLogger(__name__)

    test_default()
