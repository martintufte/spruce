from __future__ import annotations

import asyncio

from rubiks_cube.beam_search import EO_DR_HTR_PLAN
from rubiks_cube.beam_search import BeamPlan
from rubiks_cube.beam_search import BeamStep
from rubiks_cube.beam_search import beam_search
from rubiks_cube.beam_search import beam_search_async
from rubiks_cube.configuration.enumeration import Goal
from rubiks_cube.configuration.enumeration import Status
from rubiks_cube.move.generator import MoveGenerator
from rubiks_cube.move.sequence import MoveSequence


def test_plan_from_dict_template() -> None:
    template = {
        "eo-fb": {
            "max_length": 7,
            "generator": "<L, R, F, B, U, D>",
            "max_solutions": 5,
        },
        "dr-ud": {
            "max_length": 10,
            "generator": "<L, R, F2, B2, U, D>",
            "max_solutions": 3,
            "allowed_prev_goals": {"dr-ud": ["eo-fb", "eo-lr"]},
            "generator_by_prev_goal": {"eo-fb": "<L, R, F2, B2, U, D>"},
        },
    }

    plan = BeamPlan.from_dict(template, name="EO-DR")

    assert plan.name == "EO-DR"
    assert plan.steps[0].goals == [Goal.eo_fb]
    assert plan.steps[0].max_search_depth == 7
    assert plan.steps[0].n_solutions == 5
    assert plan.steps[0].generator == MoveGenerator.from_str("<L, R, F, B, U, D>")
    assert plan.steps[1].goals == [Goal.dr_ud]
    assert plan.steps[1].transition is not None
    assert plan.steps[1].transition.allowed_prev_goals == {Goal.dr_ud: [Goal.eo_fb, Goal.eo_lr]}
    assert plan.steps[1].transition.generator_by_prev_goal == {
        Goal.eo_fb: MoveGenerator.from_str("<L, R, F2, B2, U, D>")
    }


def test_beam_search_single_step() -> None:
    plan = BeamPlan.from_steps(
        steps=[
            BeamStep(
                name="solve",
                goals=[Goal.solved],
                max_search_depth=3,
                n_solutions=3,
            )
        ]
    )
    summary = beam_search(
        sequence=MoveSequence.from_str("R"),
        plan=plan,
        beam_width=3,
        n_solutions=1,
        max_time=10.0,
    )

    assert summary.status is Status.Success
    assert summary.solutions
    assert len(summary.solutions[0].sequence) == 1


def test_beam_search_async() -> None:
    plan = BeamPlan.from_steps(
        steps=[
            BeamStep(
                name="solve",
                goals=[Goal.solved],
                max_search_depth=3,
                n_solutions=2,
            )
        ]
    )
    summary = asyncio.run(
        beam_search_async(
            sequence=MoveSequence.from_str("L"),
            plan=plan,
            beam_width=2,
            n_solutions=1,
            max_time=10.0,
        )
    )

    assert summary.status is Status.Success
    assert summary.solutions
    assert len(summary.solutions[0].sequence) == 1


def test_presets_work_on_solved_cube() -> None:
    empty = MoveSequence()

    eo_summary = beam_search(
        sequence=empty,
        plan=EO_DR_HTR_PLAN,
        beam_width=2,
        n_solutions=1,
        max_time=10.0,
    )
    assert eo_summary.status is Status.Success
    assert eo_summary.solutions
    assert len(eo_summary.solutions[0].sequence) == 0


def test_multi_goal_step_on_solved_cube() -> None:
    plan = BeamPlan.from_steps(
        steps=[
            BeamStep(
                name="eo",
                goals=[Goal.eo_fb, Goal.eo_lr],
                max_search_depth=4,
                n_solutions=1,
            ),
            BeamStep(
                name="finish",
                goals=[Goal.solved],
                max_search_depth=4,
                n_solutions=1,
            ),
        ]
    )
    summary = beam_search(
        sequence=MoveSequence(),
        plan=plan,
        beam_width=2,
        n_solutions=1,
        max_time=10.0,
    )

    assert summary.status is Status.Success
    assert summary.solutions
    assert len(summary.solutions[0].sequence) == 0


def test_eo_dr_htr_scramble_solution() -> None:
    scramble = MoveSequence.from_str(
        "R' U' F D2 R L F' B D L' B' U2 R' U2 B2 D2 F2 R' B2 R D2 R' B2 F' R' U' F"
    )

    summary = beam_search(
        sequence=scramble,
        plan=EO_DR_HTR_PLAN,
        beam_width=10,
        n_solutions=1,
        max_time=60.0,
    )

    assert summary.status is Status.Success
    assert summary.solutions
    assert len(summary.solutions[0].sequence) > 0
