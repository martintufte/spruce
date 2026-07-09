from __future__ import annotations

import time
from abc import ABC
from abc import abstractmethod
from typing import TYPE_CHECKING
from typing import NamedTuple
from typing import Self

import attrs

from spruce.configuration.enumeration import SearchSide
from spruce.configuration.enumeration import Status
from spruce.move.sequence import MoveSequence
from spruce.representation.utils import invert
from spruce.solver.validators import VALIDATOR_REGISTRY
from spruce.transform.interface import SearchProblem
from spruce.transform.pipeline import Pipeline
from spruce.transform.pipeline import create_transform_pipeline
from spruce.types import BoolArray  # noqa: TC001
from spruce.types import MoveSymbol  # noqa: TC001
from spruce.types import PatternArray  # noqa: TC001
from spruce.types import PermutationArray  # noqa: TC001

if TYPE_CHECKING:
    from spruce.types import PermutationValidator


class SearchSummary[SolutionT](NamedTuple):
    solutions: list[SolutionT]
    walltime: float
    status: Status


class RootedSolution(NamedTuple):
    permutation_index: int
    sequence: MoveSequence


@attrs.define
class BaseAlgorithm(ABC):
    """Base class for search algorithms and their configuration.

    Subclasses hold algorithm-specific configuration as attrs fields and expose
    the search through ``solve``, returning rooted solutions as
    ``(root_index, moves)`` pairs, or None if no solutions were found. They
    serialize as tagged unions keyed by class name (``_type``).
    """

    @abstractmethod
    def solve(
        self,
        *,
        initial_permutations: list[PermutationArray],
        actions: dict[MoveSymbol, PermutationArray],
        pattern: PatternArray,
        adj_matrix: BoolArray,
        max_search_depth: int,
        max_solutions: int,
        max_solutions_per_root: int,
        validator: PermutationValidator | None,
        max_time: float,
    ) -> list[tuple[int, list[MoveSymbol]]] | None: ...


@attrs.define
class PermutationSolver:
    """Solve permutation search problems with a configurable search algorithm.

    Owns the compiled search problem (pipeline, actions, pattern, adjacency
    matrix); the ``algorithm`` attribute provides the search algorithm.
    """

    algorithm: BaseAlgorithm
    pipeline: Pipeline
    actions: dict[MoveSymbol, PermutationArray]
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
        algorithm: BaseAlgorithm,
        actions: dict[MoveSymbol, PermutationArray],
        pattern: PatternArray,
        validator_key: str | None = None,
        optimize_indices: bool = True,
        debug: bool = False,
    ) -> Self:
        """Initialize the solver with the given actions and pattern.

        ``optimize_indices`` reindexes indices to remove redundant positions, which
        invalidates any validator that inspects raw permutation structure. Callers
        must pass ``optimize_indices=False`` when also supplying a ``validator_key``;
        passing ``True`` with a validator raises ``ValueError`` to prevent silent
        correctness bugs.
        """
        if optimize_indices and validator_key is not None:
            raise ValueError(
                "optimize_indices=True is incompatible with a validator_key. "
                "Index optimisation reindexes indices, which invalidates validators. "
                "Pass optimize_indices=False when using a validator_key.",
            )

        pipeline = create_transform_pipeline(
            optimize_indices=optimize_indices,
            debug=debug,
        )

        search_problem = SearchProblem(
            actions=actions,
            pattern=pattern,
        )
        search_problem = pipeline.fit(search_problem)
        pipeline = pipeline.fuse()

        pattern = search_problem.pattern
        actions = search_problem.actions
        if search_problem.adj_matrix is None:
            raise ValueError("Pipeline did not set adjacency matrix on search problem.")
        adj_matrix = search_problem.adj_matrix

        return cls(
            algorithm=algorithm,
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
    def _make_sequence(solution: list[MoveSymbol], side: SearchSide) -> MoveSequence:
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
    ) -> SearchSummary[RootedSolution]:
        initial_permutations = self._prepare_permutations(permutations, side)

        start_time = time.perf_counter()
        rooted_solutions = self.algorithm.solve(
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
            return SearchSummary(
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

        return SearchSummary(
            solutions=solutions,
            walltime=walltime,
            status=Status.success,
        )
