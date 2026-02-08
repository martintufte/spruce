from __future__ import annotations

from typing import Final

from rubiks_cube.beam_search.interface import BeamPlan
from rubiks_cube.beam_search.interface import BeamStep
from rubiks_cube.beam_search.interface import Transition
from rubiks_cube.configuration.enumeration import Goal
from rubiks_cube.move.generator import MoveGenerator

EO_DR_HTR_PLAN: Final[BeamPlan] = BeamPlan.from_steps(
    name="EO-DR-HTR",
    steps=[
        BeamStep(
            goals=[Goal.eo_fb, Goal.eo_lr, Goal.eo_ud],
            max_search_depth=8,
            n_solutions=100,
            generator=MoveGenerator.from_str("<L, R, F, B, U, D>"),
            transition=Transition(side_mode="both"),
        ),
        BeamStep(
            goals=[Goal.dr_ud, Goal.dr_fb, Goal.dr_lr],
            max_search_depth=8,
            n_solutions=100,
            transition=Transition(
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
                side_mode="both",
            ),
            generator=MoveGenerator.from_str("<L, R, F, B, U, D>"),
        ),
        BeamStep(
            goals=[Goal.htr_like],
            max_search_depth=8,
            n_solutions=100,
            subset_filters={Goal.htr_like: ["real"]},
            transition=Transition(
                generator_by_prev_goal={
                    Goal.dr_ud: MoveGenerator.from_str("<L2, R2, F2, B2, U, D>"),
                    Goal.dr_lr: MoveGenerator.from_str("<L, R, F2, B2, U2, D2>"),
                    Goal.dr_fb: MoveGenerator.from_str("<L2, R2, F, B, U2, D2>"),
                },
                side_mode="both",
            ),
            generator=MoveGenerator.from_str("<L2, R2, F2, B2, U, D>"),
        ),
        BeamStep(
            goals=[Goal.solved],
            max_search_depth=8,
            n_solutions=10,
            generator=MoveGenerator.from_str("<L2, R2, F2, B2, U2, D2>"),
            transition=Transition(side_mode="same"),
        ),
    ],
)
