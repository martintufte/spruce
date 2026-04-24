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
from rubiks_cube.solver.bidirectional.beta import precompute_inverse_frontier
from rubiks_cube.solver.interface import PermutationSolver
from rubiks_cube.solver.interface import RootedSolution
from rubiks_cube.solver.interface import SearchManySummary
from rubiks_cube.solver.validators import VALIDATOR_REGISTRY
from rubiks_cube.transform.interface import SearchProblem
from rubiks_cube.transform.pipeline import Pipeline
from rubiks_cube.transform.pipeline import create_transform_pipeline

if TYPE_CHECKING:
    from rubiks_cube.configuration.types import BoolArray
    from rubiks_cube.configuration.types import PatternArray
    from rubiks_cube.configuration.types import PermutationArray
    from rubiks_cube.configuration.types import PermutationValidator


@attrs.define
class BidirectionalSolver(PermutationSolver):
    pipeline: Pipeline
    actions: dict[str, PermutationArray]
    pattern: PatternArray
    adj_matrix: BoolArray
    validator_key: str | None = None
    _inverse_frontier_cache: dict = attrs.Factory(dict)

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
        """Initialize the solver with the given actions and pattern.

        ``optimize_indices`` reindexes facelets to remove redundant positions, which
        invalidates any validator that inspects raw permutation structure. Callers
        must pass ``optimize_indices=False`` when also supplying a ``validator_key``;
        passing ``True`` with a validator raises ``ValueError`` to prevent silent
        correctness bugs.
        """
        if optimize_indices and validator_key is not None:
            raise ValueError(
                "optimize_indices=True is incompatible with a validator_key. "
                "Index optimisation reindexes facelets, which invalidates validators. "
                "Pass optimize_indices=False when using a validator_key."
            )

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
            validator_key=validator_key,
        )

    def _get_inverse_frontier(self, max_search_depth: int) -> dict[bytes, tuple[int, ...]]:
        """Return the cached inverse frontier precomputed to half of max_search_depth.

        The frontier accumulates ALL inverse states reachable within that depth so it acts as
        a complete lookup table. Because it is independent of any specific scramble it is safe
        to share across all calls to search_many that use the same solver and max_search_depth.
        """
        half_depth = max_search_depth // 2
        if half_depth not in self._inverse_frontier_cache:
            self._inverse_frontier_cache[half_depth] = precompute_inverse_frontier(
                pattern=self.pattern,
                actions=self.actions,
                adj_matrix=self.adj_matrix,
                depth=half_depth,
            )
        return self._inverse_frontier_cache[half_depth]

    def _prepare_permutations(
        self, permutations: list[PermutationArray], side: SearchSide
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
        inv_frontier = self._get_inverse_frontier(max_search_depth)

        start_time = time.perf_counter()
        rooted_solutions = bidirectional_solver(
            initial_permutations=initial_permutations,
            actions=self.actions,
            pattern=self.pattern,
            adj_matrix=self.adj_matrix,
            max_search_depth=max_search_depth,
            max_solutions=max_solutions_per_permutation * len(initial_permutations),
            max_solutions_per_root=max_solutions_per_permutation,
            validator=self.validator,
            max_time=max_time,
            prebuilt_inverse_frontier=inv_frontier,
        )
        walltime = time.perf_counter() - start_time

        if rooted_solutions is None:
            return SearchManySummary(
                solutions=[],
                walltime=walltime,
                status=Status.Failure,
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
            status=Status.Success,
        )
