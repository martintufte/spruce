from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import pytest

from rubiks_cube.configuration.regex import canonical_key
from rubiks_cube.move.generator import MoveGenerator
from rubiks_cube.move.meta import MoveMeta
from rubiks_cube.representation.pattern import get_solved_pattern
from rubiks_cube.serialization.converter import create_converter
from rubiks_cube.serialization.resources import ResourceHandler
from rubiks_cube.serialization.utils import create_session_id
from rubiks_cube.solver.actions import get_actions
from rubiks_cube.transform.action import ActionOptimizer
from rubiks_cube.transform.interface import SearchProblem
from rubiks_cube.transform.pipeline import Pipeline
from rubiks_cube.transform.pipeline import create_transform_pipeline

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def move_meta() -> MoveMeta:
    return MoveMeta.from_cube_size(3)


@pytest.fixture
def fitted_pipeline(move_meta: MoveMeta) -> tuple[Pipeline, SearchProblem, dict]:
    actions = get_actions(
        move_meta=move_meta,
        generator=MoveGenerator.from_str("<U, R>"),
    )
    original_actions = dict(actions)
    pattern = get_solved_pattern(cube_size=move_meta.cube_size)
    search_problem = SearchProblem(actions=actions, pattern=pattern, action_sort_key=canonical_key)
    pipeline = create_transform_pipeline(optimize_indices=True)
    pipeline.fit(search_problem)
    return pipeline, search_problem, original_actions


@pytest.fixture
def handler(tmp_path: Path) -> ResourceHandler:
    session_id = create_session_id()
    return ResourceHandler(resource_dir=tmp_path / session_id, converter=create_converter())


class TestPipelineRoundtrip:
    def test_pipeline_path_in_session_dir(
        self, handler: ResourceHandler, fitted_pipeline: tuple[Pipeline, SearchProblem, dict]
    ) -> None:
        pipeline, _, _actions = fitted_pipeline
        handler.save_preprocess_pipeline(pipeline)
        assert handler.pipeline_path.exists()
        assert handler.pipeline_path.parent == handler.resource_dir

    def test_transform_types_preserved(
        self, handler: ResourceHandler, fitted_pipeline: tuple[Pipeline, SearchProblem, dict]
    ) -> None:
        pipeline, _, _actions = fitted_pipeline
        handler.save_preprocess_pipeline(pipeline)
        loaded = handler.load_preprocess_pipeline()
        assert [type(t).__name__ for t in loaded.transforms] == [
            type(t).__name__ for t in pipeline.transforms
        ]

    def test_action_optimizer_state(
        self, handler: ResourceHandler, fitted_pipeline: tuple[Pipeline, SearchProblem, dict]
    ) -> None:
        pipeline, _, _actions = fitted_pipeline
        handler.save_preprocess_pipeline(pipeline)
        loaded = handler.load_preprocess_pipeline()

        original = next(t for t in pipeline.transforms if isinstance(t, ActionOptimizer))
        restored = next(t for t in loaded.transforms if isinstance(t, ActionOptimizer))

        assert restored.action_names == original.action_names
        assert restored.adj_matrix is not None
        assert original.adj_matrix is not None
        assert np.array_equal(restored.adj_matrix, original.adj_matrix)

    def test_transform_permutation_roundtrip(
        self, handler: ResourceHandler, fitted_pipeline: tuple[Pipeline, SearchProblem, dict]
    ) -> None:
        pipeline, _, original_actions = fitted_pipeline
        handler.save_preprocess_pipeline(pipeline)
        loaded = handler.load_preprocess_pipeline()

        perm = next(iter(original_actions.values()))
        assert np.array_equal(
            pipeline.transform_permutation(perm),
            loaded.transform_permutation(perm),
        )
