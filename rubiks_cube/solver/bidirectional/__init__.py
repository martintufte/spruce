from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Self  # ty: ignore[unresolved-import]

import numpy as np

from rubiks_cube.solver.bidirectional.beta import bidirectional_solver
from rubiks_cube.solver.interface import PermutationSolver
from rubiks_cube.solver.optimizers import ActionOptimizer
from rubiks_cube.solver.optimizers import IndexOptimizer

if TYPE_CHECKING:
    from rubiks_cube.configuration.types import BoolArray
    from rubiks_cube.configuration.types import CubePattern
    from rubiks_cube.configuration.types import CubePermutation


class BidirectionalSolver(PermutationSolver):
    index_optimizer: IndexOptimizer
    pattern: CubePattern
    actions: dict[str, CubePermutation]
    adj_matrix: BoolArray

    def __init__(
        self,
        index_optimizer: IndexOptimizer,
        pattern: CubePattern,
        actions: dict[str, CubePermutation],
        adj_matrix: BoolArray,
    ) -> None:
        self.index_optimizer = index_optimizer
        self.pattern = pattern
        self.actions = actions
        self.adj_matrix = adj_matrix

    @classmethod
    def from_actions_and_pattern(
        cls,
        actions: dict[str, CubePermutation],
        pattern: CubePattern,
        cube_size: int,
    ) -> Self:
        """Initialize the solver with the given actions and pattern."""

        # Optimize indices for permutation and pattern
        index_optimizer = IndexOptimizer(cube_size=cube_size)
        actions, pattern = index_optimizer.fit_transform(actions=actions, pattern=pattern)

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
        )

    def solve(
        self,
        permutation: CubePermutation,
        n_solutions: int,
        min_search_depth: int,
        max_search_depth: int,
        max_time: float,
    ) -> list[list[str]] | None:
        initial_permutation = self.index_optimizer.transform_permutation(permutation)

        return bidirectional_solver(
            initial_permutation=initial_permutation,
            actions=self.actions,
            pattern=self.pattern,
            adj_matrix=self.adj_matrix,
            min_search_depth=min_search_depth,
            max_search_depth=max_search_depth,
            n_solutions=n_solutions,
            max_time=max_time,
        )
