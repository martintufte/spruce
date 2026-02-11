from __future__ import annotations

from rubiks_cube.beam_search import EO_DR_HTR_PLAN
from rubiks_cube.beam_search import BeamPlan
from rubiks_cube.beam_search import BeamStep
from rubiks_cube.beam_search import Transition
from rubiks_cube.beam_search import beam_search
from rubiks_cube.configuration.enumeration import Goal
from rubiks_cube.configuration.enumeration import Status
from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.move.steps import MoveSteps
from rubiks_cube.move.utils import is_niss


def test_beam_search_transition_switch_solves_on_inverse() -> None:
    plan = BeamPlan.from_steps(
        name="solve-inverse",
        steps=[
            BeamStep(
                goals=[Goal.solved],
                transition=Transition(side_mode="inverse"),
                max_search_depth=1,
                n_solutions=1,
            )
        ],
    )
    summary = beam_search(
        sequence=MoveSequence.from_str("R"),
        plan=plan,
        beam_width=2,
        n_solutions=1,
        max_time=10.0,
    )

    assert summary.status is Status.Success
    assert summary.solutions
    assert len(summary.solutions[0].sequence) == 1
    assert isinstance(summary.solutions[0].steps, MoveSteps)
    assert is_niss(summary.solutions[0].sequence[0])


def test_beam_search_transition_both_keeps_both_sides() -> None:
    plan = BeamPlan.from_steps(
        name="solve-both",
        steps=[
            BeamStep(
                goals=[Goal.solved],
                transition=Transition(side_mode="both"),
                max_search_depth=1,
                n_solutions=2,
            )
        ],
    )
    summary = beam_search(
        sequence=MoveSequence.from_str("R"),
        plan=plan,
        beam_width=4,
        n_solutions=2,
        max_time=10.0,
    )

    assert summary.status is Status.Success
    assert len(summary.solutions) == 2
    sequences = {str(solution.sequence) for solution in summary.solutions}
    assert "R'" in sequences
    assert "(R)" in sequences


def test_beam_search_single_step() -> None:
    plan = BeamPlan.from_steps(
        name="solve",
        steps=[
            BeamStep(
                goals=[Goal.solved],
                max_search_depth=3,
                n_solutions=3,
            )
        ],
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
        name="eo-finish",
        steps=[
            BeamStep(
                goals=[Goal.eo_fb, Goal.eo_lr],
                max_search_depth=4,
                n_solutions=1,
            ),
            BeamStep(
                goals=[Goal.solved],
                max_search_depth=4,
                n_solutions=1,
            ),
        ],
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
        "R' U' F R' B2 R B D' F L2 B U' R2 F2 R F2 L' F2 R2 U2 F2 U2 L2 F2 R' U' F"
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
