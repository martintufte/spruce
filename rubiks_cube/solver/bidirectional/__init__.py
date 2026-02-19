from __future__ import annotations

import time
from typing import TYPE_CHECKING
from typing import Self  # ty: ignore[unresolved-import]

import attrs
import numpy as np

from rubiks_cube.configuration.enumeration import SearchSide
from rubiks_cube.configuration.enumeration import Status
from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.move.utils import niss_move
from rubiks_cube.representation.mask import get_ones_mask
from rubiks_cube.representation.permutation import get_identity_permutation
from rubiks_cube.representation.utils import invert
from rubiks_cube.solver.bidirectional.beta import bidirectional_solver
from rubiks_cube.solver.bidirectional.beta import bidirectional_solver_many
from rubiks_cube.solver.interface import PermutationSolver
from rubiks_cube.solver.interface import RootedSolution
from rubiks_cube.solver.interface import SearchManySummary
from rubiks_cube.solver.interface import SearchSummary
from rubiks_cube.solver.optimizers import ActionOptimizer
from rubiks_cube.solver.optimizers import IndexOptimizer

if TYPE_CHECKING:
    from rubiks_cube.configuration.types import BoolArray
    from rubiks_cube.configuration.types import CubePattern
    from rubiks_cube.configuration.types import CubePermutation
    from rubiks_cube.configuration.types import SolutionValidator


@attrs.frozen
class BidirectionalSolver(PermutationSolver):
    index_optimizer: IndexOptimizer
    pattern: CubePattern
    actions: dict[str, CubePermutation]
    adj_matrix: BoolArray

    solution_validator: SolutionValidator | None = None

    @classmethod
    def from_actions_and_pattern(
        cls,
        actions: dict[str, CubePermutation],
        pattern: CubePattern,
        cube_size: int,
        optimize_indices: bool = True,
        solution_validator: SolutionValidator | None = None,
    ) -> Self:
        """Initialize the solver with the given actions and pattern."""
        if solution_validator is not None:
            assert not optimize_indices

        index_optimizer = IndexOptimizer(cube_size=cube_size)
        if optimize_indices:
            actions, pattern = index_optimizer.fit_transform(actions=actions, pattern=pattern)
        else:
            identity = get_identity_permutation(cube_size=cube_size)
            mask = get_ones_mask(cube_size=cube_size)
            index_optimizer.representative_identity = identity
            index_optimizer.representative_mask = mask
            index_optimizer.affected_mask = mask.copy()
            index_optimizer.isomorphic_mask = mask.copy()
            index_optimizer.mask = mask.copy()

        # Cast pattern to uint8 for more efficinet computation and memory
        pattern = pattern.astype(np.uint8)

        # Optimize canonical order and branching factor based on action space
        action_optimizer = ActionOptimizer()
        actions = action_optimizer.fit_transform(actions=actions)
        adj_matrix = action_optimizer.get_adj_matrix()

        return cls(
            index_optimizer=index_optimizer,
            pattern=pattern,
            actions=actions,
            adj_matrix=adj_matrix,
            solution_validator=solution_validator,
        )

    def search(
        self,
        permutation: CubePermutation,
        max_solutions: int,
        min_search_depth: int,
        max_search_depth: int,
        max_time: float,
        side: SearchSide = SearchSide.normal,
    ) -> SearchSummary:
        if side is SearchSide.inverse:
            permutation = invert(permutation)

        initial_permutation = self.index_optimizer.transform_permutation(permutation)

        start_time = time.perf_counter()
        solutions = bidirectional_solver(
            initial_permutation=initial_permutation,
            actions=self.actions,
            pattern=self.pattern,
            adj_matrix=self.adj_matrix,
            min_search_depth=min_search_depth,
            max_search_depth=max_search_depth,
            max_solutions=max_solutions,
            solution_validator=self.solution_validator,
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
                solutions=[
                    MoveSequence([niss_move(move) for move in solution]) for solution in solutions
                ],
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
        permutations: list[CubePermutation],
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
            self.index_optimizer.transform_permutation(permutation)
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
            solution_validator=self.solution_validator,
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
                sequence = MoveSequence([niss_move(move) for move in solution])
            solutions.append(RootedSolution(permutation_index=root_index, sequence=sequence))

        return SearchManySummary(
            solutions=solutions,
            walltime=walltime,
            status=Status.Success,
        )
