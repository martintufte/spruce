"""IDA* solver."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING
from typing import Self

import attrs

from spruce.configuration.enumeration import SearchSide
from spruce.configuration.enumeration import Status
from spruce.configuration.regex import canonical_key
from spruce.move.sequence import MoveSequence
from spruce.representation.utils import invert
from spruce.solver.ida_star.implementation import ida_star_solver
from spruce.solver.interface import PermutationSolver
from spruce.solver.interface import RootedSolution
from spruce.solver.interface import SearchManySummary
from spruce.solver.validators import VALIDATOR_REGISTRY
from spruce.transform.interface import SearchProblem
from spruce.transform.pipeline import Pipeline
from spruce.transform.pipeline import create_transform_pipeline

if TYPE_CHECKING:
    from spruce.types import BoolArray
    from spruce.types import PatternArray
    from spruce.types import PermutationArray
    from spruce.types import PermutationValidator


@attrs.define
class IDAStarSolver(PermutationSolver):
    pipeline: Pipeline
    actions: dict[str, PermutationArray]
    pattern: PatternArray
    adj_matrix: BoolArray
    validator_key: str | None = None

    @property
    def validator(self) -> PermutationValidator | None:
        if self.validator_key is None:
            return None
        v = VALIDATOR_REGISTRY.get(self.validator_key)
        if v is None:
            raise KeyError(f"Unknown validator_key: {self.validator_key!r}")
        return v

    @classmethod
    def from_actions_and_pattern(
        cls,
        actions: dict[str, PermutationArray],
        pattern: PatternArray,
        validator_key: str | None = None,
        optimize_indices: bool = True,
        debug: bool = False,
    ) -> Self:
        """Initialize the solver with the given actions and pattern."""
        if optimize_indices and validator_key is not None:
            raise ValueError(
                "optimize_indices=True is incompatible with a validator_key. "
                "Index optimisation reindexes facelets, which invalidates validators. "
                "Pass optimize_indices=False when using a validator_key.",
            )

        pipeline = create_transform_pipeline(
            optimize_indices=optimize_indices,
            debug=debug,
        )

        search_problem = SearchProblem(
            actions=actions,
            pattern=pattern,
            action_sort_key=canonical_key,
        )
        search_problem = pipeline.fit(search_problem)
        pipeline = pipeline.fuse()

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
            validator_key=validator_key,
        )

    def _prepare_permutations(
        self,
        permutations: list[PermutationArray],
        side: SearchSide,
    ) -> list[PermutationArray]:
        if side is SearchSide.inverse:
            permutations = [invert(p) for p in permutations]
        return [self.pipeline.transform_permutation(p) for p in permutations]

    @staticmethod
    def _make_sequence(solution: list[str], side: SearchSide) -> MoveSequence:
        if side is SearchSide.inverse:
            return MoveSequence(inverse=solution)
        return MoveSequence(solution)

    def search(
        self,
        permutations: list[PermutationArray],
        max_solutions_per_permutation: int,
        max_search_depth: int,
        max_time: float,
        side: SearchSide = SearchSide.normal,
    ) -> SearchManySummary:
        initial_permutations = self._prepare_permutations(permutations, side)

        start_time = time.perf_counter()
        rooted_solutions = ida_star_solver(
            initial_permutations=initial_permutations,
            actions=self.actions,
            pattern=self.pattern,
            adj_matrix=self.adj_matrix,
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
                status=Status.failure,
            )

        solutions = [
            RootedSolution(
                permutation_index=root_index,
                sequence=self._make_sequence(solution, side),
            )
            for root_index, solution in rooted_solutions
        ]

        return SearchManySummary(
            solutions=solutions,
            walltime=walltime,
            status=Status.success,
        )
