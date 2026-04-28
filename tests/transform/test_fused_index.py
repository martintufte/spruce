from __future__ import annotations

import numpy as np
import pytest

from rubiks_cube.move.generator import MoveGenerator
from rubiks_cube.move.meta import MoveMeta
from rubiks_cube.representation.pattern import get_solved_pattern
from rubiks_cube.solver.actions import get_actions
from rubiks_cube.transform.fused_index import FusedIndexTransform
from rubiks_cube.transform.interface import IndexTransform
from rubiks_cube.transform.interface import SearchProblem
from rubiks_cube.transform.pipeline import Pipeline
from rubiks_cube.transform.pipeline import create_transform_pipeline


def make_fitted_pipeline(generator_str: str) -> tuple[dict, Pipeline]:
    move_meta = MoveMeta.from_cube_size(3)
    actions = get_actions(
        move_meta=move_meta,
        generator=MoveGenerator.from_str(generator_str),
    )
    pattern = get_solved_pattern(cube_size=move_meta.cube_size)
    problem = SearchProblem(
        actions=actions,
        pattern=pattern,
        action_sort_key=lambda _: (0, 0, 0, 0),
    )
    pipeline = create_transform_pipeline(optimize_indices=True, debug=False)
    pipeline.fit(problem)
    return actions, pipeline


TEST_GENERATORS = [
    "<R, U>",
    "<R, U, F>",
    "<R, U, D>",
    "<L2, R2, U, D, F2, B2>",
    "<M, U>",
]


class TestIndexPartsConsistency:
    """For every fitted IndexTransform, the (select, forward) pair must satisfy
    forward[p[select]] == transform_permutation(p) for every valid input p."""

    @pytest.mark.parametrize("generator_str", TEST_GENERATORS)
    def test_all_transforms(self, generator_str: str) -> None:
        actions, pipeline = make_fitted_pipeline(generator_str)
        index_transforms = [t for t in pipeline.transforms if isinstance(t, IndexTransform)]
        assert len(index_transforms) == 4, "expected 4 index transforms when optimize_indices=True"

        n_original = next(iter(actions.values())).size
        test_perms: list[np.ndarray] = [np.arange(n_original, dtype=np.uint), *actions.values()]

        for transform in index_transforms:
            select, forward = transform.index_parts()
            n_in, n_out = len(forward), len(select)

            assert forward.shape == (n_in,)
            assert select.shape == (n_out,)
            assert int(select.max()) < n_in

            for p in test_perms:
                via_parts = forward[p[select]]
                via_method = transform.transform_permutation(p)
                assert np.array_equal(via_parts, via_method), (
                    f"{type(transform).__name__}.index_parts inconsistent "
                    f"for generator '{generator_str}'"
                )

            test_perms = [transform.transform_permutation(p) for p in test_perms]


class TestFromIndexTransforms:
    """from_index_transforms must reproduce sequential application for any prefix."""

    @pytest.mark.parametrize("generator_str", TEST_GENERATORS)
    def test_full_fusion_matches_sequential(self, generator_str: str) -> None:
        actions, pipeline = make_fitted_pipeline(generator_str)
        index_transforms = [t for t in pipeline.transforms if isinstance(t, IndexTransform)]

        n_original = next(iter(actions.values())).size
        test_perms: list[np.ndarray] = [np.arange(n_original, dtype=np.uint), *actions.values()]

        fused = FusedIndexTransform.from_index_transforms(index_transforms)

        for p in test_perms:
            sequential = p.copy()
            for t in index_transforms:
                sequential = t.transform_permutation(sequential)
            assert np.array_equal(
                fused.transform_permutation(p), sequential
            ), f"Fused != sequential for generator '{generator_str}'"

    @pytest.mark.parametrize("n_transforms", [1, 2, 3, 4])
    def test_prefix_fusion_matches_sequential(self, n_transforms: int) -> None:
        actions, pipeline = make_fitted_pipeline("<R, U>")
        index_transforms = [t for t in pipeline.transforms if isinstance(t, IndexTransform)]
        subset = index_transforms[:n_transforms]

        n_original = next(iter(actions.values())).size
        test_perms: list[np.ndarray] = [np.arange(n_original, dtype=np.uint), *actions.values()]

        fused = FusedIndexTransform.from_index_transforms(subset)

        for p in test_perms:
            sequential = p.copy()
            for t in subset:
                sequential = t.transform_permutation(sequential)
            assert np.array_equal(fused.transform_permutation(p), sequential)


class TestPipelineFuse:

    @pytest.mark.parametrize("generator_str", TEST_GENERATORS)
    def test_fused_pipeline_output_matches_original(self, generator_str: str) -> None:
        actions, pipeline = make_fitted_pipeline(generator_str)
        fused_pipeline = pipeline.fuse()

        n_original = next(iter(actions.values())).size
        test_perms: list[np.ndarray] = [np.arange(n_original, dtype=np.uint), *actions.values()]

        for p in test_perms:
            assert np.array_equal(
                fused_pipeline.transform_permutation(p),
                pipeline.transform_permutation(p),
            ), f"Fused pipeline output differs for generator '{generator_str}'"

    @pytest.mark.parametrize("generator_str", TEST_GENERATORS)
    def test_fuse_replaces_index_block_with_single_transform(self, generator_str: str) -> None:
        _, pipeline = make_fitted_pipeline(generator_str)
        fused_pipeline = pipeline.fuse()

        n_index = sum(isinstance(t, IndexTransform) for t in pipeline.transforms)
        n_index_after = sum(isinstance(t, IndexTransform) for t in fused_pipeline.transforms)
        n_fused = sum(isinstance(t, FusedIndexTransform) for t in fused_pipeline.transforms)

        assert n_index == 4
        assert n_index_after == 0
        assert n_fused == 1
        assert len(fused_pipeline.transforms) == len(pipeline.transforms) - (n_index - 1)

    def test_fuse_is_noop_without_index_transforms(self) -> None:
        pipeline = create_transform_pipeline(optimize_indices=False)
        fused = pipeline.fuse()
        assert len(fused.transforms) == len(pipeline.transforms)
        assert not any(
            isinstance(t, (IndexTransform, FusedIndexTransform)) for t in fused.transforms
        )

    def test_fuse_is_idempotent(self) -> None:
        actions, pipeline = make_fitted_pipeline("<R, U>")
        fused_once = pipeline.fuse()
        fused_twice = fused_once.fuse()

        n_original = next(iter(actions.values())).size
        test_perms: list[np.ndarray] = [np.arange(n_original, dtype=np.uint), *actions.values()]

        for p in test_perms:
            assert np.array_equal(
                fused_once.transform_permutation(p),
                fused_twice.transform_permutation(p),
            )

        assert len(fused_twice.transforms) == len(fused_once.transforms)
