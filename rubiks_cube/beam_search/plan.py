from __future__ import annotations

from typing import Final

from rubiks_cube.beam_search.interface import BeamPlan
from rubiks_cube.beam_search.interface import BeamStep
from rubiks_cube.beam_search.interface import Transition
from rubiks_cube.configuration.enumeration import Goal
from rubiks_cube.move.generator import MoveGenerator

DR_PLAN: Final[BeamPlan] = BeamPlan(
    name="dr",
    steps=[
        BeamStep(
            goals=[Goal.eo_lr, Goal.eo_fb, Goal.eo_ud],
            transition=Transition(search_side="both"),
            generator=MoveGenerator.from_str("<L, R, F, B, U, D>"),
            max_search_depth=6,
            max_solutions=30,
        ),
        BeamStep(
            goals=[Goal.dr_ud, Goal.dr_fb, Goal.dr_lr],
            transition=Transition(
                search_side="both",
                generator_map={
                    Goal.eo_fb: MoveGenerator.from_str("<L, R, F2, B2, U, D>"),
                    Goal.eo_lr: MoveGenerator.from_str("<L2, R2, F, B, U, D>"),
                    Goal.eo_ud: MoveGenerator.from_str("<L, R, F, B, U2, D2>"),
                },
                check_contained=True,
                expand_variations=True,
            ),
            max_search_depth=10,
            max_solutions=10,
            generator=MoveGenerator.from_str("<L, R, F, B, U, D>"),
        ),
    ],
)

HTR_PLAN: Final[BeamPlan] = BeamPlan(
    name="htr",
    steps=[
        BeamStep(
            goals=[Goal.eo_lr, Goal.eo_fb, Goal.eo_ud],
            transition=Transition(search_side="both"),
            generator=MoveGenerator.from_str("<L, R, F, B, U, D>"),
            max_search_depth=6,
            max_solutions=30,
        ),
        BeamStep(
            goals=[Goal.dr_ud, Goal.dr_fb, Goal.dr_lr],
            transition=Transition(
                search_side="both",
                generator_map={
                    Goal.eo_fb: MoveGenerator.from_str("<L, R, F2, B2, U, D>"),
                    Goal.eo_lr: MoveGenerator.from_str("<L2, R2, F, B, U, D>"),
                    Goal.eo_ud: MoveGenerator.from_str("<L, R, F, B, U2, D2>"),
                },
                check_contained=True,
                expand_variations=True,
            ),
            max_search_depth=10,
            max_solutions=10,
            generator=MoveGenerator.from_str("<L, R, F, B, U, D>"),
        ),
        BeamStep(
            goals=[Goal.htr],
            transition=Transition(
                search_side="both",
                generator_map={
                    Goal.dr_ud: MoveGenerator.from_str("<L2, R2, F2, B2, U, D>"),
                    Goal.dr_lr: MoveGenerator.from_str("<L, R, F2, B2, U2, D2>"),
                    Goal.dr_fb: MoveGenerator.from_str("<L2, R2, F, B, U2, D2>"),
                },
                expand_variations=True,
            ),
            max_search_depth=12,
            max_solutions=10,
        ),
    ],
)

SOLVED_PLAN: Final[BeamPlan] = BeamPlan(
    name="solved",
    steps=[
        BeamStep(
            goals=[Goal.eo_lr, Goal.eo_fb, Goal.eo_ud],
            transition=Transition(search_side="both"),
            generator=MoveGenerator.from_str("<L, R, F, B, U, D>"),
            max_search_depth=6,
            max_solutions=30,
        ),
        BeamStep(
            goals=[Goal.dr_ud, Goal.dr_fb, Goal.dr_lr],
            transition=Transition(
                search_side="both",
                generator_map={
                    Goal.eo_fb: MoveGenerator.from_str("<L, R, F2, B2, U, D>"),
                    Goal.eo_lr: MoveGenerator.from_str("<L2, R2, F, B, U, D>"),
                    Goal.eo_ud: MoveGenerator.from_str("<L, R, F, B, U2, D2>"),
                },
                check_contained=True,
                expand_variations=True,
            ),
            max_search_depth=10,
            max_solutions=5,
            generator=MoveGenerator.from_str("<L, R, F, B, U, D>"),
        ),
        BeamStep(
            goals=[Goal.htr],
            transition=Transition(
                search_side="both",
                generator_map={
                    Goal.dr_ud: MoveGenerator.from_str("<L2, R2, F2, B2, U, D>"),
                    Goal.dr_lr: MoveGenerator.from_str("<L, R, F2, B2, U2, D2>"),
                    Goal.dr_fb: MoveGenerator.from_str("<L2, R2, F, B, U2, D2>"),
                },
                expand_variations=True,
            ),
            max_search_depth=12,
            max_solutions=5,
        ),
        BeamStep(
            goals=[Goal.solved],
            transition=Transition(search_side="prev", expand_variations=True),
            generator=MoveGenerator.from_str("<L2, R2, F2, B2, U2, D2>"),
            max_search_depth=14,
            max_solutions=5,
        ),
    ],
)


LEAVE_SLICE_PLAN: Final[BeamPlan] = BeamPlan(
    name="leave slice",
    steps=[
        BeamStep(
            goals=[Goal.eo_lr, Goal.eo_fb, Goal.eo_ud],
            transition=Transition(search_side="both"),
            generator=MoveGenerator.from_str("<L, R, F, B, U, D>"),
            max_search_depth=6,
            max_solutions=30,
        ),
        BeamStep(
            goals=[Goal.dr_ud, Goal.dr_fb, Goal.dr_lr],
            transition=Transition(
                search_side="both",
                generator_map={
                    Goal.eo_fb: MoveGenerator.from_str("<L, R, F2, B2, U, D>"),
                    Goal.eo_lr: MoveGenerator.from_str("<L2, R2, F, B, U, D>"),
                    Goal.eo_ud: MoveGenerator.from_str("<L, R, F, B, U2, D2>"),
                },
                check_contained=True,
                expand_variations=True,
            ),
            max_search_depth=10,
            max_solutions=10,
            generator=MoveGenerator.from_str("<L, R, F, B, U, D>"),
        ),
        BeamStep(
            goals=[Goal.htr],
            transition=Transition(
                search_side="both",
                generator_map={
                    Goal.dr_ud: MoveGenerator.from_str("<L2, R2, F2, B2, U, D>"),
                    Goal.dr_lr: MoveGenerator.from_str("<L, R, F2, B2, U2, D2>"),
                    Goal.dr_fb: MoveGenerator.from_str("<L2, R2, F, B, U2, D2>"),
                },
                expand_variations=True,
            ),
            max_search_depth=12,
            max_solutions=10,
        ),
        BeamStep(
            goals=[Goal.leave_slice_m, Goal.leave_slice_e, Goal.leave_slice_s],
            transition=Transition(search_side="prev", expand_variations=True),
            generator=MoveGenerator.from_str("<L2, R2, F2, B2, U2, D2>"),
            max_search_depth=6,
            max_solutions=10,
        ),
    ],
)

BEAM_PLANS: Final[dict[str, BeamPlan]] = {
    DR_PLAN.name: DR_PLAN,
    HTR_PLAN.name: HTR_PLAN,
    SOLVED_PLAN.name: SOLVED_PLAN,
    LEAVE_SLICE_PLAN.name: LEAVE_SLICE_PLAN,
}
