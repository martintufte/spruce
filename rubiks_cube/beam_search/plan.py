from __future__ import annotations

from typing import Final

from rubiks_cube.beam_search.interface import BeamPlan
from rubiks_cube.beam_search.interface import BeamStep
from rubiks_cube.beam_search.interface import Transition
from rubiks_cube.configuration.enumeration import Goal
from rubiks_cube.move.generator import MoveGenerator

HTR_PLAN: Final[BeamPlan] = BeamPlan(
    name="htr",
    steps=[
        BeamStep(
            goals=[Goal.eo_lr, Goal.eo_fb, Goal.eo_ud],
            transition=Transition(side_mode="both"),
            generator=MoveGenerator.from_str("<L, R, F, B, U, D>"),
            max_search_depth=6,
            max_solutions=30,
        ),
        BeamStep(
            goals=[Goal.dr_ud, Goal.dr_fb, Goal.dr_lr],
            transition=Transition(
                prev_goal_contained=True,
                generator_by_prev_goal={
                    Goal.eo_fb: MoveGenerator.from_str("<L, R, F2, B2, U, D>"),
                    Goal.eo_lr: MoveGenerator.from_str("<L2, R2, F, B, U, D>"),
                    Goal.eo_ud: MoveGenerator.from_str("<L, R, F, B, U2, D2>"),
                },
                side_mode="both",
            ),
            max_search_depth=10,
            max_solutions=10,
            generator=MoveGenerator.from_str("<L, R, F, B, U, D>"),
        ),
        BeamStep(
            goals=[Goal.htr],
            transition=Transition(
                generator_by_prev_goal={
                    Goal.dr_ud: MoveGenerator.from_str("<L2, R2, F2, B2, U, D>"),
                    Goal.dr_lr: MoveGenerator.from_str("<L, R, F2, B2, U2, D2>"),
                    Goal.dr_fb: MoveGenerator.from_str("<L2, R2, F, B, U2, D2>"),
                },
                side_mode="both",
            ),
            max_search_depth=12,
            max_solutions=10,
        ),
        BeamStep(
            goals=[Goal.solved],
            transition=Transition(side_mode="normal"),
            generator=MoveGenerator.from_str("<L2, R2, F2, B2, U2, D2>"),
            max_search_depth=12,
            max_solutions=10,
        ),
    ],
)

BLOCKS_PLAN: Final[BeamPlan] = BeamPlan(
    name="blocks",
    steps=[
        BeamStep(
            goals=[Goal.block_2x2x2],
            max_search_depth=8,
            max_solutions=10,
            generator=MoveGenerator.from_str("<L, R, F, B, U, D>"),
            transition=Transition(side_mode="both"),
        ),
        BeamStep(
            goals=[Goal.block_2x2x3],
            max_search_depth=8,
            max_solutions=10,
            generator=MoveGenerator.from_str("<L, R, F, B, U, D>"),
            transition=Transition(prev_goal_contained=True, side_mode="both"),
        ),
    ],
)
