"""IDA* solver."""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import ClassVar

import attrs

from spruce.solver.ida_star.implementation import ida_star_solver
from spruce.solver.interface import BaseAlgorithm

if TYPE_CHECKING:
    from spruce.types import BoolArray
    from spruce.types import PatternArray
    from spruce.types import PermutationArray
    from spruce.types import PermutationValidator


@attrs.define
class IDAStarAlgorithm(BaseAlgorithm):
    """Iterative-deepening depth-first search with a pluggable heuristic.

    Algorithm configuration (e.g. pruning-table heuristics) belongs here as
    attrs fields and is forwarded to the implementation in ``solve``.
    """

    name: ClassVar[str] = "ida_star"

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
        return ida_star_solver(
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
