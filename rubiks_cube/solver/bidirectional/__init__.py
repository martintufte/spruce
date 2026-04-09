"""Bidirectional solver."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING
from typing import Self

import attrs

from rubiks_cube.configuration.enumeration import SearchSide
from rubiks_cube.configuration.enumeration import Status
from rubiks_cube.configuration.regex import canonical_key
from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.representation.utils import invert
from rubiks_cube.solver.bidirectional.beta import bidirectional_solver
from rubiks_cube.solver.bidirectional.beta import bidirectional_solver_many
from rubiks_cube.solver.interface import PermutationSolver
from rubiks_cube.solver.interface import RootedSolution
from rubiks_cube.solver.interface import SearchManySummary
from rubiks_cube.solver.interface import SearchSummary
from rubiks_cube.transform.interface import SearchProblem
from rubiks_cube.transform.pipeline import create_transform_pipeline

if TYPE_CHECKING:
    from rubiks_cube.configuration.types import BoolArray
    from rubiks_cube.configuration.types import PatternArray
    from rubiks_cube.configuration.types import PermutationArray
    from rubiks_cube.configuration.types import PermutationValidator
    from rubiks_cube.transform.pipeline import Pipeline


@attrs.frozen
class BidirectionalSolver(PermutationSolver):
    pipeline: Pipeline
    actions: dict[str, PermutationArray]
    pattern: PatternArray
    adj_matrix: BoolArray
    validator: PermutationValidator | None

    @classmethod
    def from_actions_and_pattern(
        cls,
        actions: dict[str, PermutationArray],
        pattern: PatternArray,
        validator: PermutationValidator | None = None,
        optimize_indices: bool = True,
        debug: bool = False,
    ) -> Self:
        """Initialize the solver with the given actions and pattern."""
        optimize_indices &= validator is None

        pipeline = create_transform_pipeline(
            optimize_indices=optimize_indices,
            debug=debug,
        )

        search_problem = SearchProblem(
            actions=actions, pattern=pattern, action_sort_key=canonical_key
        )
        search_problem = pipeline.fit(search_problem)

        pattern = search_problem.pattern
        actions = search_problem.actions
        if search_problem.adj_matrix is None:
            raise ValueError("Pipeline did not set adjacency matrix on search problem.")
        adj_matrix = search_problem.adj_matrix

        return cls(
            pipeline=pipeline,
            pattern=pattern,
            actions=actions,
            adj_matrix=adj_matrix,
            validator=validator,
        )

    def search(
        self,
        permutation: PermutationArray,
        max_solutions: int,
        min_search_depth: int,
        max_search_depth: int,
        max_time: float,
        side: SearchSide = SearchSide.normal,
    ) -> SearchSummary:
        if side is SearchSide.inverse:
            permutation = invert(permutation)

        initial_permutation = self.pipeline.transform_permutation(permutation)

        start_time = time.perf_counter()
        solutions = bidirectional_solver(
            initial_permutation=initial_permutation,
            actions=self.actions,
            pattern=self.pattern,
            adj_matrix=self.adj_matrix,
            min_search_depth=min_search_depth,
            max_search_depth=max_search_depth,
            max_solutions=max_solutions,
            validator=self.validator,
            max_time=max_time,
        )
        walltime = time.perf_counter() - start_time

        if solutions is None:
            return SearchSummary(
                solutions=[],
                walltime=walltime,
                status=Status.Failure,
            )

        if side is SearchSide.inverse:
            return SearchSummary(
                solutions=[MoveSequence(inverse=solution) for solution in solutions],
                walltime=walltime,
                status=Status.Success,
            )

        return SearchSummary(
            solutions=[MoveSequence(solution) for solution in solutions],
            walltime=walltime,
            status=Status.Success,
        )

    def search_many(
        self,
        permutations: list[PermutationArray],
        max_solutions_per_permutation: int,
        min_search_depth: int,
        max_search_depth: int,
        max_time: float,
        side: SearchSide = SearchSide.normal,
    ) -> SearchManySummary:
        transformed_permutations = permutations
        if side is SearchSide.inverse:
            transformed_permutations = [invert(permutation) for permutation in permutations]

        initial_permutations = [
            self.pipeline.transform_permutation(permutation)
            for permutation in transformed_permutations
        ]

        start_time = time.perf_counter()
        rooted_solutions = bidirectional_solver_many(
            initial_permutations=initial_permutations,
            actions=self.actions,
            pattern=self.pattern,
            adj_matrix=self.adj_matrix,
            min_search_depth=min_search_depth,
            max_search_depth=max_search_depth,
            max_solutions=max_solutions_per_permutation * len(initial_permutations),
            max_solutions_per_root=max_solutions_per_permutation,
            validator=self.validator,
            max_time=max_time,
        )
        walltime = time.perf_counter() - start_time

        if rooted_solutions is None:
            return SearchManySummary(
                solutions=[],
                walltime=walltime,
                status=Status.Failure,
            )

        solutions: list[RootedSolution] = []
        for root_index, solution in rooted_solutions:
            sequence = MoveSequence(solution)
            if side is SearchSide.inverse:
                sequence = MoveSequence(inverse=solution)
            solutions.append(RootedSolution(permutation_index=root_index, sequence=sequence))

        return SearchManySummary(
            solutions=solutions,
            walltime=walltime,
            status=Status.Success,
        )
