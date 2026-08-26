from __future__ import annotations

from functools import partial

from spruce.algebra.sequence import MoveSequence
from spruce.autotagger.pattern import get_catalogue
from spruce.puzzle.cube.goals import Goal
from spruce.puzzle.cube.group import build_move_meta
from spruce.puzzle.cube.metrics import Metric
from spruce.puzzle.cube.metrics import measure
from spruce.puzzle.cube.notation import parse_moves
from spruce.puzzle.cube.plans import HTR_PLAN
from spruce.puzzle.cube.spec import Puzzle
from spruce.puzzle.cube.variants import Variant
from spruce.search.beam import beam_search
from spruce.search.beam import build_step_contexts
from spruce.search.beam.interface import BeamPlan
from spruce.search.beam.interface import BeamStep
from spruce.search.beam.interface import SearchSideChoice
from spruce.search.beam.interface import Transition
from spruce.search.enumeration import Status
from spruce.types import GoalId
from spruce.types import VariantId

MOVE_META = build_move_meta(puzzle=Puzzle._3x3x3)
CATALOGUE = get_catalogue(puzzle=Puzzle._3x3x3)
COST = partial(measure, metric=Metric.HTM)


def test_beam_search_transition_switch_solves_on_inverse() -> None:
    plan = BeamPlan(
        name="solve-inverse",
        steps=(
            BeamStep(
                goal=GoalId(Goal.solved.value),
                variants=[VariantId(Variant.none.value)],
                transition=Transition(
                    search_side=SearchSideChoice.inverse,
                    generator_map={
                        VariantId(Variant.none.value): MOVE_META.to_symbols(
                            "L", "R", "F", "B", "U", "D"
                        ),
                    },
                ),
                max_search_depth=1,
                max_solutions=1,
            ),
        ),
    )
    summary = beam_search(
        sequence=parse_moves("R"),
        plan=plan,
        move_meta=MOVE_META,
        beam_width=2,
        cost=COST,
        patterns=CATALOGUE,
        max_solutions=1,
        max_time=10.0,
    )

    assert summary.status is Status.success
    assert summary.solutions
    assert len(summary.solutions[0].sequence) == 1
    assert isinstance(summary.solutions[0].steps, tuple)
    assert len(summary.solutions[0].sequence.inverse) > 0


def test_beam_search_transition_both_keeps_both_sides() -> None:
    plan = BeamPlan(
        name="solve-both",
        steps=(
            BeamStep(
                goal=GoalId(Goal.solved.value),
                variants=[VariantId(Variant.none.value)],
                transition=Transition(
                    search_side=SearchSideChoice.both,
                    generator_map={
                        VariantId(Variant.none.value): MOVE_META.to_symbols(
                            "L", "R", "F", "B", "U", "D"
                        ),
                    },
                ),
                max_search_depth=1,
                max_solutions=2,
            ),
        ),
    )
    summary = beam_search(
        sequence=parse_moves("R"),
        plan=plan,
        move_meta=MOVE_META,
        beam_width=2,
        cost=COST,
        patterns=CATALOGUE,
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
        steps=(
            BeamStep(
                goal=GoalId(Goal.solved.value),
                variants=[VariantId(Variant.none.value)],
                transition=Transition(
                    search_side=SearchSideChoice.prev,
                    generator_map={
                        VariantId(Variant.none.value): MOVE_META.to_symbols(
                            "L", "R", "F", "B", "U", "D"
                        ),
                    },
                ),
                max_search_depth=3,
                max_solutions=3,
            ),
        ),
    )
    summary = beam_search(
        sequence=parse_moves("R"),
        plan=plan,
        move_meta=MOVE_META,
        beam_width=3,
        cost=COST,
        patterns=CATALOGUE,
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
        move_meta=MOVE_META,
        beam_width=2,
        cost=COST,
        patterns=CATALOGUE,
        max_solutions=1,
        max_time=10.0,
    )
    assert htr_summary.status is Status.success
    assert htr_summary.solutions
    assert len(htr_summary.solutions[0].sequence) == 0


def test_multi_goal_step_on_solved_cube() -> None:
    plan = BeamPlan(
        name="eo-finish",
        steps=(
            BeamStep(
                goal=GoalId(Goal.eo.value),
                variants=[VariantId(Variant.fb.value), VariantId(Variant.lr.value)],
                transition=Transition(
                    generator_map={
                        VariantId(Variant.none.value): MOVE_META.to_symbols(
                            "L", "R", "F", "B", "U", "D"
                        ),
                    },
                ),
                max_search_depth=4,
                max_solutions=1,
            ),
            BeamStep(
                goal=GoalId(Goal.solved.value),
                variants=[VariantId(Variant.none.value)],
                transition=Transition(
                    generator_map={
                        VariantId(Variant.fb.value): MOVE_META.to_symbols(
                            "L", "R", "F", "B", "U", "D"
                        ),
                        VariantId(Variant.lr.value): MOVE_META.to_symbols(
                            "L", "R", "F", "B", "U", "D"
                        ),
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
        move_meta=MOVE_META,
        beam_width=2,
        cost=COST,
        patterns=CATALOGUE,
        max_solutions=1,
        max_time=10.0,
    )

    assert summary.status is Status.success
    assert summary.solutions
    assert len(summary.solutions[0].sequence) == 0


def test_prev_goal_contained_allows_matching_transition() -> None:
    plan = BeamPlan(
        name="eo-dr",
        steps=(
            BeamStep(
                goal=GoalId(Goal.eo.value),
                variants=[VariantId(Variant.fb.value)],
                transition=Transition(
                    generator_map={
                        VariantId(Variant.none.value): MOVE_META.to_symbols(
                            "L", "R", "F", "B", "U", "D"
                        ),
                    },
                ),
                max_search_depth=0,
                max_solutions=1,
            ),
            BeamStep(
                goal=GoalId(Goal.dr.value),
                variants=[VariantId(Variant.ud.value)],
                transition=Transition(
                    search_side=SearchSideChoice.prev,
                    generator_map={
                        VariantId(Variant.fb.value): MOVE_META.to_symbols(
                            "L", "R", "F", "B", "U", "D"
                        ),
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
        move_meta=MOVE_META,
        beam_width=2,
        cost=COST,
        patterns=CATALOGUE,
        max_solutions=1,
        max_time=10.0,
    )

    assert summary.status is Status.success
    assert summary.solutions
    assert len(summary.solutions[0].sequence) == 0


def test_prev_goal_contained_rejects_non_matching_transition() -> None:
    plan = BeamPlan(
        name="eo-dr not contained",
        steps=(
            BeamStep(
                goal=GoalId(Goal.eo.value),
                variants=[VariantId(Variant.fb.value)],
                transition=Transition(
                    generator_map={
                        VariantId(Variant.none.value): MOVE_META.to_symbols(
                            "L", "R", "F", "B", "U", "D"
                        ),
                    },
                ),
                max_search_depth=0,
                max_solutions=1,
            ),
            BeamStep(
                goal=GoalId(Goal.dr.value),
                variants=[VariantId(Variant.fb.value)],
                transition=Transition(
                    search_side=SearchSideChoice.prev,
                    generator_map={
                        VariantId(Variant.fb.value): MOVE_META.to_symbols(
                            "L", "R", "F", "B", "U", "D"
                        ),
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
        move_meta=MOVE_META,
        beam_width=2,
        cost=COST,
        patterns=CATALOGUE,
        max_solutions=1,
        max_time=10.0,
    )

    assert summary.status is Status.failure
    assert summary.solutions == []


def test_htr_step_uses_solution_validator() -> None:
    puzzle = Puzzle._3x3x3
    plan = BeamPlan(
        name="htr-validator",
        steps=(
            BeamStep(
                goal=GoalId(Goal.htr.value),
                variants=[VariantId(Variant.none.value)],
                transition=Transition(
                    generator_map={
                        VariantId(Variant.none.value): MOVE_META.to_symbols(
                            "L", "R", "F", "B", "U", "D"
                        ),
                    },
                ),
                max_search_depth=1,
                max_solutions=1,
            ),
            BeamStep(
                goal=GoalId(Goal.solved.value),
                variants=[VariantId(Variant.none.value)],
                transition=Transition(
                    generator_map={
                        VariantId(Variant.none.value): MOVE_META.to_symbols(
                            "L", "R", "F", "B", "U", "D"
                        ),
                    },
                ),
                max_search_depth=1,
                max_solutions=1,
            ),
        ),
    )
    move_meta = build_move_meta(puzzle=puzzle)

    contexts = build_step_contexts(plan=plan, move_meta=move_meta, patterns=CATALOGUE)
    htr_contexts = contexts[0].contexts_for_prev_variant(prev_variant=VariantId(Variant.none.value))
    solved_contexts = contexts[1].contexts_for_prev_variant(
        prev_variant=VariantId(Variant.none.value)
    )

    assert len(htr_contexts) == 1
    assert len(solved_contexts) == 1
    assert htr_contexts[0].goal == GoalId(Goal.htr.value)
    assert solved_contexts[0].goal == GoalId(Goal.solved.value)
    assert htr_contexts[0].solver.validator is not None
    assert solved_contexts[0].solver.validator is None


def test_eo_dr_htr_scramble_solution() -> None:
    scramble = parse_moves(
        "R' U' F R' B2 R B D' F L2 B U' R2 F2 R F2 L' F2 R2 U2 F2 U2 L2 F2 R' U' F",
    )

    summary = beam_search(
        sequence=scramble,
        plan=HTR_PLAN,
        move_meta=MOVE_META,
        beam_width=2,
        cost=COST,
        patterns=CATALOGUE,
        max_solutions=1,
        max_time=60.0,
    )

    assert summary.status is Status.success
    assert summary.solutions
    assert len(summary.solutions[0].sequence) > 0
