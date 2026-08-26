from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import pytest

from spruce.algebra import get_permutation
from spruce.parsing import parse_generator
from spruce.puzzle.cube.group import build_move_meta
from spruce.puzzle.cube.notation import parse_moves
from spruce.puzzle.cube.patterns import get_solved_pattern
from spruce.puzzle.cube.spec import Puzzle
from spruce.search.transform.action import compute_adjacency_matrix
from spruce.search.transform.cast import CastDtype
from spruce.search.transform.cast import get_index_dtype
from spruce.search.transform.index import DisjointSubsetReorderer
from spruce.search.transform.index import FilterAffected
from spruce.search.transform.index import FilterIsomorphic
from spruce.search.transform.index import FilterRepresentative
from spruce.search.transform.interface import SearchProblem
from spruce.search.transform.pipeline import Pipeline
from spruce.search.transform.pipeline import create_transform_pipeline
from spruce.types import MoveSymbol

if TYPE_CHECKING:
    from spruce.algebra.sequence import MoveSequence
    from spruce.types import PermutationArray


@pytest.fixture
def default_pipeline() -> Pipeline:
    return create_transform_pipeline(
        optimize_indices=True,
        debug=False,
    )


class TestIndexOptimizer:
    puzzle = Puzzle._3x3x3
    move_meta = build_move_meta(puzzle=puzzle)

    def _assert_transform_sizes(
        self,
        default_pipeline: Pipeline,
        actions: dict[MoveSymbol, PermutationArray],
        representative_size: int,
        affected_size: int,
        isomorphic_size: int,
        subset_sizes: list[int],
    ) -> None:
        pattern = get_solved_pattern(puzzle=Puzzle._3x3x3)
        search_problem = SearchProblem(
            actions=actions,
            pattern=pattern,
        )

        search_problem = default_pipeline.fit(search_problem=search_problem)
        transformed_size = next(iter(search_problem.actions.values())).size
        expected_dtype = get_index_dtype(transformed_size)
        assert search_problem.pattern.dtype == np.uint8
        assert all(perm.dtype == expected_dtype for perm in search_problem.actions.values())

        for transform in default_pipeline.transforms:
            if isinstance(transform, FilterRepresentative):
                assert transform.representative_mask is not None
                assert sum(transform.representative_mask) == representative_size
            elif isinstance(transform, FilterAffected):
                assert transform.affected_mask is not None
                assert sum(transform.affected_mask) == affected_size
            elif isinstance(transform, FilterIsomorphic):
                assert transform.isomorphic_mask is not None
                assert sum(transform.isomorphic_mask) == isomorphic_size
            elif isinstance(transform, DisjointSubsetReorderer):
                assert transform.subset_sizes is not None
                assert transform.subset_sizes == subset_sizes
            elif isinstance(transform, CastDtype):
                assert transform.permutation_dtype == expected_dtype

    @pytest.mark.parametrize(
        (
            "generator_str",
            "representative_size",
            "affected_size",
            "isomorphic_size",
            "subset_sizes",
        ),
        [
            ("<L, R, U, D, F, B>", 54, 48, 48, [24, 24]),
            ("<R, U>", 38, 32, 25, [7, 18]),
            ("<R, U, F>", 45, 39, 39, [18, 21]),
            ("<R, U, D>", 50, 44, 34, [10, 24]),
            ("<L2, R2, U, D, F2, B2>", 54, 48, 20, [4, 8, 8]),
            ("<L2, R2, U2, D2, F2, B2>", 54, 48, 20, [4, 4, 4, 4, 4]),
            ("<M, U>", 26, 20, 20, [4, 4, 12]),
        ],
    )
    def test_generators(
        self,
        default_pipeline: Pipeline,
        generator_str: str,
        representative_size: int,
        affected_size: int,
        isomorphic_size: int,
        subset_sizes: list[int],
    ) -> None:
        generator = parse_generator(generator_str, move_meta=self.move_meta)
        actions = self.move_meta.get_actions(generator=generator)
        self._assert_transform_sizes(
            default_pipeline=default_pipeline,
            actions=actions,
            representative_size=representative_size,
            affected_size=affected_size,
            isomorphic_size=isomorphic_size,
            subset_sizes=subset_sizes,
        )

    @pytest.mark.parametrize(
        ("algorithm", "representative_size", "affected_size", "isomorphic_size", "subset_sizes"),
        [
            (
                parse_moves("R U R' U' R' F R2 U' R' U' R U R' F'"),  # T-perm
                12,
                6,
                2,
                [2],
            ),
            (
                parse_moves("M2 U M U2 M' U M2"),  # Ua-perm
                9,
                3,
                3,
                [3],
            ),
        ],
    )
    def test_algorithms(
        self,
        default_pipeline: Pipeline,
        algorithm: MoveSequence,
        representative_size: int,
        affected_size: int,
        isomorphic_size: int,
        subset_sizes: list[int],
    ) -> None:
        # TODO: Build via move_meta.get_actions once algorithms are represented in MoveMeta
        actions = {
            MoveSymbol(str(algorithm)): get_permutation(
                sequence=algorithm,
                move_meta=self.move_meta,
            ),
        }
        self._assert_transform_sizes(
            default_pipeline=default_pipeline,
            actions=actions,
            representative_size=representative_size,
            affected_size=affected_size,
            isomorphic_size=isomorphic_size,
            subset_sizes=subset_sizes,
        )


def test_compute_adjacency_matrix_handles_empty_permutations() -> None:
    adj_matrix = compute_adjacency_matrix(((), ()), 0)
    assert adj_matrix.shape == (2, 2)
    assert not adj_matrix.any()


@pytest.mark.parametrize(
    ("size", "expected_dtype"),
    [
        (256, np.dtype(np.uint8)),
        (257, np.dtype(np.uint16)),
        (65536, np.dtype(np.uint16)),
        (65537, np.dtype(np.uint32)),
    ],
)
def test_get_index_dtype(size: int, expected_dtype: np.dtype[np.unsignedinteger]) -> None:
    assert get_index_dtype(size) == expected_dtype
