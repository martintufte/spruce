from __future__ import annotations

from rubiks_cube.beam_search.interface import BeamPlan
from rubiks_cube.beam_search.interface import BeamStep
from rubiks_cube.beam_search.interface import SearchSideChoice
from rubiks_cube.beam_search.interface import Transition
from rubiks_cube.beam_search.plan import HTR_PLAN
from rubiks_cube.beam_search.solver import beam_search
from rubiks_cube.beam_search.solver import build_step_contexts
from rubiks_cube.configuration.enumeration import Goal
from rubiks_cube.configuration.enumeration import Status
from rubiks_cube.configuration.enumeration import Variant
from rubiks_cube.move.generator import MoveGenerator
from rubiks_cube.move.meta import MoveMeta
from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.move.steps import MoveSteps


def test_beam_search_transition_switch_solves_on_inverse() -> None:
    plan = BeamPlan(
        name="solve-inverse",
        cube_size=3,
        steps=(
            BeamStep(
                goal=Goal.solved,
                variants=[Variant.none],
                transition=Transition(
                    search_side=SearchSideChoice.inverse,
                    generator_map={
                        Variant.none: MoveGenerator.from_str("<L, R, F, B, U, D>"),
                    },
                ),
                max_search_depth=1,
                max_solutions=1,
            ),
        ),
    )
    summary = beam_search(
        sequence=MoveSequence.from_str("R"),
        plan=plan,
        beam_width=2,
        max_solutions=1,
        max_time=10.0,
    )

    assert summary.status is Status.success
    assert summary.solutions
    assert len(summary.solutions[0].sequence) == 1
    assert isinstance(summary.solutions[0].steps, MoveSteps)
    assert len(summary.solutions[0].sequence.inverse) > 0


def test_beam_search_transition_both_keeps_both_sides() -> None:
    plan = BeamPlan(
        name="solve-both",
        cube_size=3,
        steps=(
            BeamStep(
                goal=Goal.solved,
                variants=[Variant.none],
                transition=Transition(
                    search_side=SearchSideChoice.both,
                    generator_map={
                        Variant.none: MoveGenerator.from_str("<L, R, F, B, U, D>"),
                    },
                ),
                max_search_depth=1,
                max_solutions=2,
            ),
        ),
    )
    summary = beam_search(
        sequence=MoveSequence.from_str("R"),
        plan=plan,
        beam_width=2,
        max_solutions=2,
        max_time=10.0,
    )

    assert summary.status is Status.success
    assert len(summary.solutions) == 2
    sequences = {str(solution.sequence) for solution in summary.solutions}
    assert "R'" in sequences
    assert "(R)" in sequences


def test_beam_search_single_step() -> None:
    plan = BeamPlan(
        name="solve",
        cube_size=3,
        steps=(
            BeamStep(
                goal=Goal.solved,
                variants=[Variant.none],
                transition=Transition(
                    search_side=SearchSideChoice.prev,
                    generator_map={
                        Variant.none: MoveGenerator.from_str("<L, R, F, B, U, D>"),
                    },
                ),
                max_search_depth=3,
                max_solutions=3,
            ),
        ),
    )
    summary = beam_search(
        sequence=MoveSequence.from_str("R"),
        plan=plan,
        beam_width=3,
        max_solutions=1,
        max_time=10.0,
    )

    assert summary.status is Status.success
    assert summary.solutions
    assert len(summary.solutions[0].sequence) == 1


def test_presets_work_on_solved_cube() -> None:
    empty_sequence = MoveSequence()

    htr_summary = beam_search(
        sequence=empty_sequence,
        plan=HTR_PLAN,
        beam_width=2,
        max_solutions=1,
        max_time=10.0,
    )
    assert htr_summary.status is Status.success
    assert htr_summary.solutions
    assert len(htr_summary.solutions[0].sequence) == 0


def test_multi_goal_step_on_solved_cube() -> None:
    plan = BeamPlan(
        name="eo-finish",
        cube_size=3,
        steps=(
            BeamStep(
                goal=Goal.eo,
                variants=[Variant.fb, Variant.lr],
                transition=Transition(
                    generator_map={
                        Variant.none: MoveGenerator.from_str("<L, R, F, B, U, D>"),
                    },
                ),
                max_search_depth=4,
                max_solutions=1,
            ),
            BeamStep(
                goal=Goal.solved,
                variants=[Variant.none],
                transition=Transition(
                    generator_map={
                        Variant.fb: MoveGenerator.from_str("<L, R, F, B, U, D>"),
                        Variant.lr: MoveGenerator.from_str("<L, R, F, B, U, D>"),
                    },
                ),
                max_search_depth=4,
                max_solutions=1,
            ),
        ),
    )
    summary = beam_search(
        sequence=MoveSequence(),
        plan=plan,
        beam_width=2,
        max_solutions=1,
        max_time=10.0,
    )

    assert summary.status is Status.success
    assert summary.solutions
    assert len(summary.solutions[0].sequence) == 0


def test_prev_goal_contained_allows_matching_transition() -> None:
    plan = BeamPlan(
        name="eo-dr",
        cube_size=3,
        steps=(
            BeamStep(
                goal=Goal.eo,
                variants=[Variant.fb],
                transition=Transition(
                    generator_map={
                        Variant.none: MoveGenerator.from_str("<L, R, F, B, U, D>"),
                    },
                ),
                max_search_depth=0,
                max_solutions=1,
            ),
            BeamStep(
                goal=Goal.dr,
                variants=[Variant.ud],
                transition=Transition(
                    search_side=SearchSideChoice.prev,
                    generator_map={
                        Variant.fb: MoveGenerator.from_str("<L, R, F, B, U, D>"),
                    },
                    check_contained=True,
                ),
                max_search_depth=0,
                max_solutions=1,
            ),
        ),
    )

    summary = beam_search(
        sequence=MoveSequence(),
        plan=plan,
        beam_width=2,
        max_solutions=1,
        max_time=10.0,
    )

    assert summary.status is Status.success
    assert summary.solutions
    assert len(summary.solutions[0].sequence) == 0


def test_prev_goal_contained_rejects_non_matching_transition() -> None:
    plan = BeamPlan(
        name="eo-dr not contained",
        cube_size=3,
        steps=(
            BeamStep(
                goal=Goal.eo,
                variants=[Variant.fb],
                transition=Transition(
                    generator_map={
                        Variant.none: MoveGenerator.from_str("<L, R, F, B, U, D>"),
                    },
                ),
                max_search_depth=0,
                max_solutions=1,
            ),
            BeamStep(
                goal=Goal.dr,
                variants=[Variant.fb],
                transition=Transition(
                    search_side=SearchSideChoice.prev,
                    generator_map={
                        Variant.fb: MoveGenerator.from_str("<L, R, F, B, U, D>"),
                    },
                    check_contained=True,
                ),
                max_search_depth=0,
                max_solutions=1,
            ),
        ),
    )

    summary = beam_search(
        sequence=MoveSequence(),
        plan=plan,
        beam_width=2,
        max_solutions=1,
        max_time=10.0,
    )

    assert summary.status is Status.failure
    assert summary.solutions == []


def test_htr_step_uses_solution_validator() -> None:
    plan = BeamPlan(
        name="htr-validator",
        cube_size=3,
        steps=(
            BeamStep(
                goal=Goal.htr,
                variants=[Variant.none],
                transition=Transition(
                    generator_map={
                        Variant.none: MoveGenerator.from_str("<L, R, F, B, U, D>"),
                    },
                ),
                max_search_depth=1,
                max_solutions=1,
            ),
            BeamStep(
                goal=Goal.solved,
                variants=[Variant.none],
                transition=Transition(
                    generator_map={
                        Variant.none: MoveGenerator.from_str("<L, R, F, B, U, D>"),
                    },
                ),
                max_search_depth=1,
                max_solutions=1,
            ),
        ),
    )
    move_meta = MoveMeta.from_cube_size(3)

    contexts = build_step_contexts(plan=plan, move_meta=move_meta)
    htr_contexts = contexts[0].contexts_for_prev_variant(prev_variant=Variant.none)
    solved_contexts = contexts[1].contexts_for_prev_variant(prev_variant=Variant.none)

    assert len(htr_contexts) == 1
    assert len(solved_contexts) == 1
    assert htr_contexts[0].goal is Goal.htr
    assert solved_contexts[0].goal is Goal.solved
    assert htr_contexts[0].solver.validator is not None
    assert solved_contexts[0].solver.validator is None


def test_eo_dr_htr_scramble_solution() -> None:
    scramble = MoveSequence.from_str(
        "R' U' F R' B2 R B D' F L2 B U' R2 F2 R F2 L' F2 R2 U2 F2 U2 L2 F2 R' U' F"
    )

    summary = beam_search(
        sequence=scramble,
        plan=HTR_PLAN,
        beam_width=2,
        max_solutions=1,
        max_time=60.0,
    )

    assert summary.status is Status.success
    assert summary.solutions
    assert len(summary.solutions[0].sequence) > 0
