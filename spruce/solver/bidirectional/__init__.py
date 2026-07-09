"""Bidirectional solver."""

from __future__ import annotations

from typing import TYPE_CHECKING

import attrs

from spruce.solver.bidirectional.implementation import bidirectional_solver
from spruce.solver.interface import BaseAlgorithm

if TYPE_CHECKING:
    from spruce.types import BoolArray
    from spruce.types import PatternArray
    from spruce.types import PermutationArray
    from spruce.types import PermutationValidator


@attrs.define
class BidirectionalAlgorithm(BaseAlgorithm):
    """Breadth-first search from both the scramble and the goal, meeting in the middle."""


    def solve(
        self,
        *,
        initial_permutations: list[PermutationArray],
        actions: dict[str, PermutationArray],
        pattern: PatternArray,
        adj_matrix: BoolArray,
        max_search_depth: int,
        max_solutions: int,
        max_solutions_per_root: int,
        validator: PermutationValidator | None,
        max_time: float,
    ) -> list[tuple[int, list[str]]] | None:
        return bidirectional_solver(
            initial_permutations=initial_permutations,
            actions=actions,
            pattern=pattern,
            adj_matrix=adj_matrix,
            max_search_depth=max_search_depth,
            max_solutions=max_solutions,
            max_solutions_per_root=max_solutions_per_root,
            validator=validator,
            max_time=max_time,
        )
