from __future__ import annotations

from typing import Final

from rubiks_cube.beam_search.interface import BeamPlan
from rubiks_cube.beam_search.interface import BeamStep
from rubiks_cube.beam_search.interface import Transition
from rubiks_cube.configuration.enumeration import Goal
from rubiks_cube.configuration.enumeration import Variant
from rubiks_cube.move.generator import MoveGenerator

DR_PLAN: Final[BeamPlan] = BeamPlan(
    name="dr",
    cube_size=3,
    steps=[
        BeamStep(
            goal=Goal.eo,
            variants=[Variant.lr, Variant.fb, Variant.ud],
            transition=Transition(
                search_side="both",
                generator_map={
                    Variant.none: MoveGenerator.from_str("<L, R, F, B, U, D>"),
                },
            ),
            max_search_depth=6,
            max_solutions=30,
        ),
        BeamStep(
            goal=Goal.dr,
            variants=[Variant.lr, Variant.fb, Variant.ud],
            transition=Transition(
                search_side="both",
                generator_map={
                    Variant.lr: MoveGenerator.from_str("<L2, R2, F, B, U, D>"),
                    Variant.fb: MoveGenerator.from_str("<L, R, F2, B2, U, D>"),
                    Variant.ud: MoveGenerator.from_str("<L, R, F, B, U2, D2>"),
                },
                check_contained=True,
                expand_candidate=True,
            ),
            max_search_depth=10,
            max_solutions=10,
        ),
    ],
)

HTR_PLAN: Final[BeamPlan] = BeamPlan(
    name="htr",
    cube_size=3,
    steps=[
        BeamStep(
            goal=Goal.eo,
            variants=[Variant.lr, Variant.fb, Variant.ud],
            transition=Transition(
                search_side="both",
                generator_map={
                    Variant.none: MoveGenerator.from_str("<L, R, F, B, U, D>"),
                },
            ),
            max_search_depth=6,
            max_solutions=30,
        ),
        BeamStep(
            goal=Goal.dr,
            variants=[Variant.lr, Variant.fb, Variant.ud],
            transition=Transition(
                search_side="both",
                generator_map={
                    Variant.lr: MoveGenerator.from_str("<L2, R2, F, B, U, D>"),
                    Variant.fb: MoveGenerator.from_str("<L, R, F2, B2, U, D>"),
                    Variant.ud: MoveGenerator.from_str("<L, R, F, B, U2, D2>"),
                },
                check_contained=True,
                expand_candidate=True,
            ),
            max_search_depth=10,
            max_solutions=10,
        ),
        BeamStep(
            goal=Goal.htr,
            variants=[Variant.none],
            transition=Transition(
                search_side="both",
                generator_map={
                    Variant.lr: MoveGenerator.from_str("<L, R, F2, B2, U2, D2>"),
                    Variant.ud: MoveGenerator.from_str("<L2, R2, F2, B2, U, D>"),
                    Variant.fb: MoveGenerator.from_str("<L2, R2, F, B, U2, D2>"),
                },
                expand_candidate=True,
            ),
            max_search_depth=12,
            max_solutions=10,
        ),
    ],
)

SOLVED_PLAN: Final[BeamPlan] = BeamPlan(
    name="solved",
    cube_size=3,
    steps=[
        BeamStep(
            goal=Goal.eo,
            variants=[Variant.lr, Variant.fb, Variant.ud],
            transition=Transition(
                search_side="both",
                generator_map={
                    Variant.none: MoveGenerator.from_str("<L, R, F, B, U, D>"),
                },
            ),
            max_search_depth=6,
            max_solutions=30,
        ),
        BeamStep(
            goal=Goal.dr,
            variants=[Variant.lr, Variant.fb, Variant.ud],
            transition=Transition(
                search_side="both",
                generator_map={
                    Variant.lr: MoveGenerator.from_str("<L2, R2, F, B, U, D>"),
                    Variant.fb: MoveGenerator.from_str("<L, R, F2, B2, U, D>"),
                    Variant.ud: MoveGenerator.from_str("<L, R, F, B, U2, D2>"),
                },
                check_contained=True,
                expand_candidate=True,
            ),
            max_search_depth=10,
            max_solutions=10,
        ),
        BeamStep(
            goal=Goal.htr,
            variants=[Variant.none],
            transition=Transition(
                search_side="both",
                generator_map={
                    Variant.lr: MoveGenerator.from_str("<L, R, F2, B2, U2, D2>"),
                    Variant.fb: MoveGenerator.from_str("<L2, R2, F, B, U2, D2>"),
                    Variant.ud: MoveGenerator.from_str("<L2, R2, F2, B2, U, D>"),
                },
                expand_candidate=True,
            ),
            max_search_depth=12,
            max_solutions=10,
        ),
        BeamStep(
            goal=Goal.solved,
            variants=[Variant.none],
            transition=Transition(
                search_side="prev",
                generator_map={
                    Variant.none: MoveGenerator.from_str("<L2, R2, F2, B2, U2, D2>"),
                },
                expand_candidate=True,
            ),
            max_search_depth=12,
            max_solutions=5,
        ),
    ],
)


LEAVE_SLICE_PLAN: Final[BeamPlan] = BeamPlan(
    name="leave slice",
    cube_size=3,
    steps=[
        BeamStep(
            goal=Goal.eo,
            variants=[Variant.lr, Variant.fb, Variant.ud],
            transition=Transition(
                search_side="both",
                generator_map={
                    Variant.none: MoveGenerator.from_str("<L, R, F, B, U, D>"),
                },
            ),
            max_search_depth=6,
            max_solutions=30,
        ),
        BeamStep(
            goal=Goal.dr,
            variants=[Variant.lr, Variant.fb, Variant.ud],
            transition=Transition(
                search_side="both",
                generator_map={
                    Variant.lr: MoveGenerator.from_str("<L2, R2, F, B, U, D>"),
                    Variant.fb: MoveGenerator.from_str("<L, R, F2, B2, U, D>"),
                    Variant.ud: MoveGenerator.from_str("<L, R, F, B, U2, D2>"),
                },
                check_contained=True,
                expand_candidate=True,
            ),
            max_search_depth=10,
            max_solutions=10,
        ),
        BeamStep(
            goal=Goal.htr,
            variants=[Variant.none],
            transition=Transition(
                search_side="both",
                generator_map={
                    Variant.lr: MoveGenerator.from_str("<L, R, F2, B2, U2, D2>"),
                    Variant.fb: MoveGenerator.from_str("<L2, R2, F, B, U2, D2>"),
                    Variant.ud: MoveGenerator.from_str("<L2, R2, F2, B2, U, D>"),
                },
                expand_candidate=True,
            ),
            max_search_depth=12,
            max_solutions=10,
        ),
        BeamStep(
            goal=Goal.solved,
            variants=[Variant.none],
            transition=Transition(
                search_side="prev",
                generator_map={
                    Variant.none: MoveGenerator.from_str("<L2, R2, F2, B2, U2, D2>"),
                },
                expand_candidate=True,
            ),
            max_search_depth=12,
            max_solutions=5,
        ),
        BeamStep(
            goal=Goal.leave_slice,
            variants=[Variant.lr, Variant.fb, Variant.ud],
            transition=Transition(
                search_side="prev",
                generator_map={
                    Variant.lr: MoveGenerator.from_str("<L2, R2, F2, B2, U2, D2>"),
                    Variant.fb: MoveGenerator.from_str("<L2, R2, F2, B2, U2, D2>"),
                    Variant.ud: MoveGenerator.from_str("<L2, R2, F2, B2, U2, D2>"),
                },
                allowed_variants_by_prev_variant={
                    Variant.lr: frozenset({Variant.lr}),
                    Variant.fb: frozenset({Variant.fb}),
                    Variant.ud: frozenset({Variant.ud}),
                },
                prev_goal_index=-2,
                expand_candidate=True,
            ),
            max_search_depth=10,
            max_solutions=10,
        ),
    ],
)

BEAM_PLANS: Final[dict[str, BeamPlan]] = {
    SOLVED_PLAN.name: SOLVED_PLAN,
    LEAVE_SLICE_PLAN.name: LEAVE_SLICE_PLAN,
    HTR_PLAN.name: HTR_PLAN,
    DR_PLAN.name: DR_PLAN,
}
