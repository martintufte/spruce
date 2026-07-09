from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import pytest

from spruce.beam_search.interface import BeamPlan
from spruce.beam_search.plan import DR_PLAN
from spruce.beam_search.solver import CompiledStep
from spruce.beam_search.solver import build_step_contexts
from spruce.configuration.enumeration import Puzzle
from spruce.configuration.enumeration import SearchSide
from spruce.configuration.regex import canonical_key
from spruce.move.meta import MoveMeta
from spruce.move.sequence import MoveSequence
from spruce.representation import get_rubiks_cube_permutation
from spruce.representation.pattern import get_solved_pattern
from spruce.serialization.converter import create_converter
from spruce.serialization.resources import ResourceHandler
from spruce.serialization.utils import create_session_id
from spruce.solver.bidirectional import BidirectionalAlgorithm
from spruce.solver.ida_star import IDAStarAlgorithm
from spruce.solver.interface import BaseAlgorithm
from spruce.solver.unidirectional import UnidirectionalAlgorithm
from spruce.transform.action import ActionOptimizer
from spruce.transform.interface import SearchProblem
from spruce.transform.pipeline import Pipeline
from spruce.transform.pipeline import create_transform_pipeline

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def move_meta() -> MoveMeta:
    return MoveMeta.from_puzzle(Puzzle._3x3x3)


@pytest.fixture
def fitted_pipeline(move_meta: MoveMeta) -> tuple[Pipeline, SearchProblem, dict]:
    actions = move_meta.get_actions(generator=frozenset({"U", "R"}))
    original_actions = dict(actions)
    pattern = get_solved_pattern(puzzle=move_meta.puzzle)
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
        self,
        handler: ResourceHandler,
        fitted_pipeline: tuple[Pipeline, SearchProblem, dict],
    ) -> None:
        pipeline, _, _actions = fitted_pipeline
        handler.save_preprocess_pipeline(pipeline)
        assert handler.pipeline_path.exists()
        assert handler.pipeline_path.parent == handler.resource_dir

    def test_transform_types_preserved(
        self,
        handler: ResourceHandler,
        fitted_pipeline: tuple[Pipeline, SearchProblem, dict],
    ) -> None:
        pipeline, _, _actions = fitted_pipeline
        handler.save_preprocess_pipeline(pipeline)
        loaded = handler.load_preprocess_pipeline()
        assert [type(t).__name__ for t in loaded.transforms] == [
            type(t).__name__ for t in pipeline.transforms
        ]

    def test_action_optimizer_state(
        self,
        handler: ResourceHandler,
        fitted_pipeline: tuple[Pipeline, SearchProblem, dict],
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
        self,
        handler: ResourceHandler,
        fitted_pipeline: tuple[Pipeline, SearchProblem, dict],
    ) -> None:
        pipeline, _, original_actions = fitted_pipeline
        handler.save_preprocess_pipeline(pipeline)
        loaded = handler.load_preprocess_pipeline()

        perm = next(iter(original_actions.values()))
        assert np.array_equal(
            pipeline.transform_permutation(perm),
            loaded.transform_permutation(perm),
        )


@pytest.fixture
def step_contexts(move_meta: MoveMeta) -> list[CompiledStep]:
    plan = BeamPlan(
        name="eo-only",
        puzzle=Puzzle._3x3x3,
        steps=(DR_PLAN.steps[0],),  # single EO step — fast to build
    )
    return build_step_contexts(plan=plan, move_meta=move_meta)


class TestStepContextsRoundtrip:
    def test_step_contexts_path_in_session_dir(
        self,
        handler: ResourceHandler,
        step_contexts: list[CompiledStep],
    ) -> None:
        handler.save_step_contexts(step_contexts)
        assert handler.step_contexts_path.exists()
        assert handler.step_contexts_path.parent == handler.resource_dir

    def test_step_count_preserved(
        self,
        handler: ResourceHandler,
        step_contexts: list[CompiledStep],
    ) -> None:
        handler.save_step_contexts(step_contexts)
        loaded = handler.load_step_contexts()
        assert len(loaded) == len(step_contexts)

    def test_solver_pattern_preserved(
        self,
        handler: ResourceHandler,
        step_contexts: list[CompiledStep],
    ) -> None:
        handler.save_step_contexts(step_contexts)
        loaded = handler.load_step_contexts()

        for orig_opts, loaded_opts in zip(step_contexts, loaded, strict=True):
            for gen_key in orig_opts.contexts_by_generator:
                for orig_ctx, loaded_ctx in zip(
                    orig_opts.contexts_by_generator[gen_key],
                    loaded_opts.contexts_by_generator[gen_key],
                    strict=True,
                ):
                    assert np.array_equal(orig_ctx.solver.pattern, loaded_ctx.solver.pattern)
                    assert np.array_equal(orig_ctx.solver.adj_matrix, loaded_ctx.solver.adj_matrix)

    def test_solver_inference_equivalent(
        self,
        handler: ResourceHandler,
        step_contexts: list[CompiledStep],
    ) -> None:
        handler.save_step_contexts(step_contexts)
        loaded = handler.load_step_contexts()

        move_meta = MoveMeta.from_puzzle(puzzle=Puzzle._3x3x3)
        scramble = MoveSequence(["F", "U", "R"])
        permutation = get_rubiks_cube_permutation(sequence=scramble, move_meta=move_meta)

        for orig_opts, loaded_opts in zip(step_contexts, loaded, strict=True):
            for gen_key in orig_opts.contexts_by_generator:
                for orig_ctx, loaded_ctx in zip(
                    orig_opts.contexts_by_generator[gen_key],
                    loaded_opts.contexts_by_generator[gen_key],
                    strict=True,
                ):
                    orig_result = orig_ctx.solver.search(
                        permutations=[permutation],
                        max_solutions_per_permutation=1,
                        max_search_depth=4,
                        max_time=5.0,
                        side=SearchSide.normal,
                    )
                    loaded_result = loaded_ctx.solver.search(
                        permutations=[permutation],
                        max_solutions_per_permutation=1,
                        max_search_depth=4,
                        max_time=5.0,
                        side=SearchSide.normal,
                    )
                    assert orig_result.status == loaded_result.status


def test_algorithm_roundtrip_by_type_tag() -> None:
    converter = create_converter()
    for algorithm in (BidirectionalAlgorithm(), UnidirectionalAlgorithm(), IDAStarAlgorithm()):
        data = converter.unstructure(algorithm)
        assert data["_type"] == type(algorithm).__name__
        assert converter.structure(data, BaseAlgorithm) == algorithm


def test_structure_unknown_algorithm_type_raises() -> None:
    converter = create_converter()
    with pytest.raises(KeyError, match="DoesNotExist"):
        converter.structure({"_type": "DoesNotExist"}, BaseAlgorithm)
