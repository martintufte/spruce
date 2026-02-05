from __future__ import annotations

from typing import Final

from rubiks_cube.beam_search.models import BeamPlan
from rubiks_cube.beam_search.models import BeamStep
from rubiks_cube.beam_search.models import TransitionSpec
from rubiks_cube.configuration.enumeration import Goal
from rubiks_cube.move.generator import MoveGenerator

EO_DR_HTR_PLAN: Final[BeamPlan] = BeamPlan.from_steps(
    name="EO-DR-HTR",
    steps=[
        BeamStep(
            name="eo",
            goals=[Goal.eo_fb, Goal.eo_lr, Goal.eo_ud],
            max_search_depth=7,
            n_solutions=1,
            search_solutions=20,
            generator=MoveGenerator.from_str("<L, R, F, B, U, D>"),
        ),
        BeamStep(
            name="dr",
            goals=[Goal.dr_ud, Goal.dr_fb, Goal.dr_lr],
            max_search_depth=10,
            n_solutions=1,
            search_solutions=10,
            transition=TransitionSpec(
                allowed_prev_goals={
                    Goal.dr_ud: [Goal.eo_fb, Goal.eo_lr],
                    Goal.dr_fb: [Goal.eo_lr, Goal.eo_ud],
                    Goal.dr_lr: [Goal.eo_fb, Goal.eo_ud],
                },
                generator_by_prev_goal={
                    Goal.eo_fb: MoveGenerator.from_str("<L, R, F2, B2, U, D>"),
                    Goal.eo_lr: MoveGenerator.from_str("<L2, R2, F, B, U, D>"),
                    Goal.eo_ud: MoveGenerator.from_str("<L, R, F, B, U2, D2>"),
                },
            ),
            generator=MoveGenerator.from_str("<L, R, F, B, U, D>"),
        ),
        BeamStep(
            name="htr",
            goals=[Goal.htr_like],
            max_search_depth=12,
            n_solutions=1,
            search_solutions=50,
            subset_filters=["real"],
            transition=TransitionSpec(
                generator_by_prev_goal={
                    Goal.dr_ud: MoveGenerator.from_str("<L2, R2, F2, B2, U, D>"),
                    Goal.dr_lr: MoveGenerator.from_str("<L, R, F2, B2, U2, D2>"),
                    Goal.dr_fb: MoveGenerator.from_str("<L2, R2, F, B, U2, D2>"),
                }
            ),
            generator=MoveGenerator.from_str("<L2, R2, F2, B2, U, D>"),
        ),
        BeamStep(
            name="finish",
            goals=[Goal.solved],
            max_search_depth=10,
            n_solutions=1,
            generator=MoveGenerator.from_str("<L2, R2, F2, B2, U2, D2>"),
        ),
    ],
)
