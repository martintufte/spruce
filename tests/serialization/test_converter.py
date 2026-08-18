from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import pytest

from spruce.algebra import get_permutation
from spruce.autotagger.subset import is_real_htr
from spruce.beam_search.interface import BeamPlan
from spruce.beam_search.plan import DR_PLAN
from spruce.beam_search.solver import CompiledStep
from spruce.beam_search.solver import build_step_contexts
from spruce.move.sequence import MoveSequence
from spruce.puzzle.cube.group import build_move_meta
from spruce.puzzle.cube.patterns import get_solved_pattern
from spruce.puzzle.cube.spec import Puzzle
from spruce.search.bidirectional import BidirectionalSolver
from spruce.search.enumeration import SearchSide
from spruce.search.transform.action import ActionOptimizer
from spruce.search.transform.interface import SearchProblem
from spruce.search.transform.pipeline import Pipeline
from spruce.search.transform.pipeline import create_transform_pipeline
from spruce.serialization.converter import create_converter
from spruce.serialization.resources import ResourceHandler
from spruce.serialization.utils import create_session_id
from spruce.types import MoveSymbol

if TYPE_CHECKING:
    from pathlib import Path

    from spruce.algebra.group import MoveMeta


@pytest.fixture
def move_meta() -> MoveMeta:
    return build_move_meta(Puzzle._3x3x3)


@pytest.fixture
def fitted_pipeline(move_meta: MoveMeta) -> tuple[Pipeline, SearchProblem, dict]:
    actions = move_meta.get_actions(generator=frozenset({MoveSymbol("U"), MoveSymbol("R")}))
    original_actions = dict(actions)
    pattern = get_solved_pattern(puzzle=Puzzle._3x3x3)
    search_problem = SearchProblem(actions=actions, pattern=pattern)
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
        pipeline, _search_problem, _actions = fitted_pipeline
        handler.save_preprocess_pipeline(pipeline)
        assert handler.pipeline_path.exists()
        assert handler.pipeline_path.parent == handler.resource_dir

    def test_transform_types_preserved(
        self,
        handler: ResourceHandler,
        fitted_pipeline: tuple[Pipeline, SearchProblem, dict],
    ) -> None:
        pipeline, _search_problem, _actions = fitted_pipeline
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
        pipeline, _search_problem, _actions = fitted_pipeline
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
        pipeline, _search_problem, original_actions = fitted_pipeline
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

        move_meta = build_move_meta(puzzle=Puzzle._3x3x3)
        scramble = MoveSequence.from_str("F U R")
        permutation = get_permutation(sequence=scramble, move_meta=move_meta)

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


class TestValidatorRoundtrip:
    """A validator is a callable, so only its name survives serialization.

    The converter has to resolve that name back to the callable; if it does not, a
    deserialized solver would silently accept permutations the validator rejects.
    """

    def test_validator_is_restored_from_its_key(self, move_meta: MoveMeta) -> None:
        converter = create_converter()
        solver = BidirectionalSolver.from_actions_and_pattern(
            actions=move_meta.get_actions(generator=move_meta.to_symbols("U")),
            pattern=get_solved_pattern(puzzle=Puzzle._3x3x3),
            validator=is_real_htr,
            validator_key="htr",
            optimize_indices=False,
        )

        restored = converter.structure(converter.unstructure(solver), BidirectionalSolver)

        assert restored.validator_key == "htr"
        assert restored.validator is is_real_htr

    def test_solver_without_validator_round_trips_as_none(self, move_meta: MoveMeta) -> None:
        converter = create_converter()
        solver = BidirectionalSolver.from_actions_and_pattern(
            actions=move_meta.get_actions(generator=move_meta.to_symbols("U")),
            pattern=get_solved_pattern(puzzle=Puzzle._3x3x3),
        )

        restored = converter.structure(converter.unstructure(solver), BidirectionalSolver)

        assert restored.validator_key is None
        assert restored.validator is None

    def test_unknown_validator_key_is_rejected(self, move_meta: MoveMeta) -> None:
        converter = create_converter()
        solver = BidirectionalSolver.from_actions_and_pattern(
            actions=move_meta.get_actions(generator=move_meta.to_symbols("U")),
            pattern=get_solved_pattern(puzzle=Puzzle._3x3x3),
            validator=is_real_htr,
            validator_key="htr",
            optimize_indices=False,
        )
        data = converter.unstructure(solver)
        data["validator_key"] = "not-a-validator"

        with pytest.raises(ValueError, match="Unknown validator_key"):
            converter.structure(data, BidirectionalSolver)
