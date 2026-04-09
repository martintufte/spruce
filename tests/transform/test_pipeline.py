from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import pytest

from rubiks_cube.configuration import DEFAULT_GENERATOR_MAP
from rubiks_cube.move.algorithm import MoveAlgorithm
from rubiks_cube.move.generator import MoveGenerator
from rubiks_cube.move.meta import MoveMeta
from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.representation.pattern import get_solved_pattern
from rubiks_cube.solver.actions import get_actions
from rubiks_cube.transform.action import compute_adjacency_matrix
from rubiks_cube.transform.cast import CastDtype
from rubiks_cube.transform.cast import get_index_dtype
from rubiks_cube.transform.index import DisjointSubsetReorderer
from rubiks_cube.transform.index import FilterAffected
from rubiks_cube.transform.index import FilterIsomorphic
from rubiks_cube.transform.index import FilterRepresentative
from rubiks_cube.transform.interface import SearchProblem
from rubiks_cube.transform.pipeline import Pipeline
from rubiks_cube.transform.pipeline import create_transform_pipeline

if TYPE_CHECKING:
    from rubiks_cube.configuration.types import PermutationArray


@pytest.fixture
def default_pipeline() -> Pipeline:
    return create_transform_pipeline(
        optimize_indices=True,
        debug=False,
    )


class TestIndexOptimizer:
    move_meta = MoveMeta.from_cube_size(3)

    def _assert_transform_sizes(
        self,
        default_pipeline: Pipeline,
        actions: dict[str, PermutationArray],
        representative_size: int,
        affected_size: int,
        isomorphic_size: int,
        subset_sizes: list[int],
    ) -> None:
        pattern = get_solved_pattern(cube_size=self.move_meta.cube_size)
        search_problem = SearchProblem(
            actions=actions, pattern=pattern, action_sort_key=lambda _: (0, 0, 0, 0)
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
        "generator_str,representative_size,affected_size,isomorphic_size,subset_sizes",
        [
            (DEFAULT_GENERATOR_MAP[3], 54, 48, 48, [24, 24]),
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
        actions = get_actions(
            move_meta=self.move_meta,
            generator=MoveGenerator.from_str(generator_str),
        )
        self._assert_transform_sizes(
            default_pipeline=default_pipeline,
            actions=actions,
            representative_size=representative_size,
            affected_size=affected_size,
            isomorphic_size=isomorphic_size,
            subset_sizes=subset_sizes,
        )

    @pytest.mark.parametrize(
        "algorithm,representative_size,affected_size,isomorphic_size,subset_sizes",
        [
            (
                MoveAlgorithm(
                    "T-perm",
                    MoveSequence.from_str("R U R' U' R' F R2 U' R' U' R U R' F'"),
                ),
                12,
                6,
                2,
                [2],
            ),
            (
                MoveAlgorithm("Ua-perm", MoveSequence.from_str("M2 U M U2 M' U M2")),
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
        algorithm: MoveAlgorithm,
        representative_size: int,
        affected_size: int,
        isomorphic_size: int,
        subset_sizes: list[int],
    ) -> None:
        actions = get_actions(move_meta=self.move_meta, algorithms=[algorithm])
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
    "size,expected_dtype",
    [
        (256, np.dtype(np.uint8)),
        (257, np.dtype(np.uint16)),
        (65536, np.dtype(np.uint16)),
        (65537, np.dtype(np.uint32)),
    ],
)
def test_get_index_dtype(size: int, expected_dtype: np.dtype[np.unsignedinteger]) -> None:
    assert get_index_dtype(size) == expected_dtype
