from __future__ import annotations

import numpy as np
import pytest

from spruce.configuration.enumeration import Puzzle
from spruce.configuration.enumeration import SearchSide
from spruce.configuration.enumeration import Status
from spruce.move.meta import MoveMeta
from spruce.move.sequence import MoveSequence
from spruce.representation import get_rubiks_cube_permutation
from spruce.solver.bidirectional import BidirectionalAlgorithm
from spruce.solver.bidirectional.implementation import bidirectional_solver
from spruce.solver.interface import BaseAlgorithm
from spruce.solver.interface import PermutationSolver

ALGORITHMS = [BidirectionalAlgorithm()]

MOVE_META = MoveMeta.from_puzzle(puzzle=Puzzle._3x3x3)
IDENTITY_PATTERN = np.arange(54, dtype=np.uint8)


def permutation_of(scramble: str):
    return get_rubiks_cube_permutation(
        sequence=MoveSequence.from_str(scramble),
        move_meta=MOVE_META,
    )


@pytest.mark.parametrize("algorithm", ALGORITHMS)
class TestPermutationSolverContract:
    def test_search_returns_rooted_solutions(self, algorithm: BaseAlgorithm) -> None:
        actions = MOVE_META.get_actions(generator=frozenset({"R"}))
        solver = PermutationSolver.from_actions_and_pattern(
            algorithm=algorithm,
            actions=actions,
            pattern=IDENTITY_PATTERN,
            optimize_indices=False,
        )

        summary = solver.search(
            permutations=[permutation_of("R"), permutation_of("R'")],
            max_solutions_per_permutation=1,
            max_search_depth=1,
            max_time=10.0,
            side=SearchSide.normal,
        )

        assert summary.status is Status.success
        assert len(summary.solutions) == 2
        by_root = {
            solution.permutation_index: str(solution.sequence) for solution in summary.solutions
        }
        assert by_root[0] == "R'"
        assert by_root[1] == "R"

    @pytest.mark.parametrize(
        ("scramble", "optimal_length"),
        [
            ("R U", 2),
            ("R U2 F'", 3),
            ("R U R' F", 4),
        ],
    )
    def test_finds_optimal_solution_length(
        self,
        algorithm: BaseAlgorithm,
        scramble: str,
        optimal_length: int,
    ) -> None:
        actions = MOVE_META.get_actions(generator=frozenset({"U", "R", "F"}))
        solver = PermutationSolver.from_actions_and_pattern(
            algorithm=algorithm,
            actions=actions,
            pattern=IDENTITY_PATTERN,
            optimize_indices=False,
        )

        summary = solver.search(
            permutations=[permutation_of(scramble)],
            max_solutions_per_permutation=1,
            max_search_depth=optimal_length,
            max_time=30.0,
            side=SearchSide.normal,
        )

        assert summary.status is Status.success
        assert len(summary.solutions) == 1
        assert len(summary.solutions[0].sequence) == optimal_length

    def test_already_solved_permutation(self, algorithm: BaseAlgorithm) -> None:
        actions = MOVE_META.get_actions(generator=frozenset({"R"}))
        solver = PermutationSolver.from_actions_and_pattern(
            algorithm=algorithm,
            actions=actions,
            pattern=IDENTITY_PATTERN,
            optimize_indices=False,
        )

        summary = solver.search(
            permutations=[permutation_of("")],
            max_solutions_per_permutation=1,
            max_search_depth=1,
            max_time=10.0,
            side=SearchSide.normal,
        )

        assert summary.status is Status.success
        assert len(summary.solutions) == 1
        assert len(summary.solutions[0].sequence) == 0

    def test_inverse_side_returns_inverse_sequence(self, algorithm: BaseAlgorithm) -> None:
        actions = MOVE_META.get_actions(generator=frozenset({"R"}))
        solver = PermutationSolver.from_actions_and_pattern(
            algorithm=algorithm,
            actions=actions,
            pattern=IDENTITY_PATTERN,
            optimize_indices=False,
        )

        summary = solver.search(
            permutations=[permutation_of("R")],
            max_solutions_per_permutation=1,
            max_search_depth=1,
            max_time=10.0,
            side=SearchSide.inverse,
        )

        assert summary.status is Status.success
        assert len(summary.solutions) == 1
        assert len(summary.solutions[0].sequence.inverse) > 0

    def test_failure_when_out_of_depth(self, algorithm: BaseAlgorithm) -> None:
        actions = MOVE_META.get_actions(generator=frozenset({"U", "R"}))
        solver = PermutationSolver.from_actions_and_pattern(
            algorithm=algorithm,
            actions=actions,
            pattern=IDENTITY_PATTERN,
            optimize_indices=False,
        )

        summary = solver.search(
            permutations=[permutation_of("R U R' U'")],
            max_solutions_per_permutation=1,
            max_search_depth=1,
            max_time=10.0,
            side=SearchSide.normal,
        )

        assert summary.status is Status.failure
        assert summary.solutions == []

    def test_optimize_indices_rejected_with_validator(self, algorithm: BaseAlgorithm) -> None:
        actions = MOVE_META.get_actions(generator=frozenset({"R"}))
        with pytest.raises(ValueError, match="optimize_indices"):
            PermutationSolver.from_actions_and_pattern(
                algorithm=algorithm,
                actions=actions,
                pattern=IDENTITY_PATTERN,
                validator_key="htr",
                optimize_indices=True,
            )


@pytest.mark.parametrize("solver_fn", [bidirectional_solver])
def test_rejecting_validator_yields_no_solutions(solver_fn) -> None:
    actions = MOVE_META.get_actions(generator=frozenset({"R"}))
    adj_matrix = np.ones((len(actions), len(actions)), dtype=bool)

    result = solver_fn(
        initial_permutations=[permutation_of("R")],
        actions=actions,
        pattern=IDENTITY_PATTERN,
        adj_matrix=adj_matrix,
        max_search_depth=2,
        max_solutions=1,
        max_solutions_per_root=1,
        validator=lambda _permutation: False,
        max_time=10.0,
    )

    assert result is None
