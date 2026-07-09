"""Unidirectional brute-force solver."""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import ClassVar

import attrs

from spruce.solver.interface import BaseAlgorithm
from spruce.solver.unidirectional.implementation import unidirectional_solver

if TYPE_CHECKING:
    from spruce.types import BoolArray
    from spruce.types import PatternArray
    from spruce.types import PermutationArray
    from spruce.types import PermutationValidator


@attrs.define
class UnidirectionalAlgorithm(BaseAlgorithm):
    """Breadth-first search from the scramble only, checking states against the goal."""

    name: ClassVar[str] = "unidirectional"

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
        return unidirectional_solver(
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
