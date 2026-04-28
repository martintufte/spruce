from __future__ import annotations

from enum import Enum
from typing import Final

from rubiks_cube.beam_search.interface import BeamPlan
from rubiks_cube.beam_search.interface import BeamStep
from rubiks_cube.beam_search.interface import SearchSideChoice
from rubiks_cube.beam_search.interface import Transition
from rubiks_cube.configuration.enumeration import Goal
from rubiks_cube.configuration.enumeration import Variant
from rubiks_cube.move.generator import MoveGenerator

EO_STEP: Final[BeamStep] = BeamStep(
    goal=Goal.eo,
    variants=[Variant.lr, Variant.fb, Variant.ud],
    transition=Transition(
        search_side=SearchSideChoice.both,
        generator_map={
            Variant.none: MoveGenerator.from_str("<L, R, F, B, U, D>"),
        },
    ),
    max_search_depth=6,
    max_solutions=30,
)

DR_STEP: Final[BeamStep] = BeamStep(
    goal=Goal.dr,
    variants=[Variant.lr, Variant.fb, Variant.ud],
    transition=Transition(
        search_side=SearchSideChoice.both,
        generator_map={
            Variant.lr: MoveGenerator.from_str("<L2, R2, F, B, U, D>"),
            Variant.fb: MoveGenerator.from_str("<L, R, F2, B2, U, D>"),
            Variant.ud: MoveGenerator.from_str("<L, R, F, B, U2, D2>"),
        },
        check_contained=True,
    ),
    max_search_depth=10,
    max_solutions=10,
)

HTR_STEP: Final[BeamStep] = BeamStep(
    goal=Goal.htr,
    variants=[Variant.none],
    transition=Transition(
        search_side=SearchSideChoice.both,
        generator_map={
            Variant.lr: MoveGenerator.from_str("<L, R, F2, B2, U2, D2>"),
            Variant.fb: MoveGenerator.from_str("<L2, R2, F, B, U2, D2>"),
            Variant.ud: MoveGenerator.from_str("<L2, R2, F2, B2, U, D>"),
        },
    ),
    max_search_depth=12,
    max_solutions=10,
)

FINISH_STEP: Final[BeamStep] = BeamStep(
    goal=Goal.solved,
    variants=[Variant.none],
    transition=Transition(
        search_side=SearchSideChoice.prev,
        generator_map={
            Variant.none: MoveGenerator.from_str("<L2, R2, F2, B2, U2, D2>"),
        },
    ),
    max_search_depth=12,
    max_solutions=5,
)

LEAVE_SLICE_STEP: Final[BeamStep] = BeamStep(
    goal=Goal.leave_slice,
    variants=[Variant.lr, Variant.fb, Variant.ud],
    transition=Transition(
        search_side=SearchSideChoice.prev,
        generator_map={
            Variant.none: MoveGenerator.from_str("<L2, R2, F2, B2, U2, D2>"),
        },
    ),
    max_search_depth=10,
    max_solutions=10,
)

DR_PLAN: Final[BeamPlan] = BeamPlan(
    name="dr",
    cube_size=3,
    steps=(EO_STEP, DR_STEP),
)

HTR_PLAN: Final[BeamPlan] = BeamPlan(
    name="htr",
    cube_size=3,
    steps=(EO_STEP, DR_STEP, HTR_STEP),
)

SOLVED_PLAN: Final[BeamPlan] = BeamPlan(
    name="solved",
    cube_size=3,
    steps=(EO_STEP, DR_STEP, HTR_STEP, FINISH_STEP),
)

LEAVE_SLICE_PLAN: Final[BeamPlan] = BeamPlan(
    name="leave slice",
    cube_size=3,
    steps=(EO_STEP, DR_STEP, HTR_STEP, FINISH_STEP, LEAVE_SLICE_STEP),
)


class PlanName(Enum):
    dr = "dr"
    htr = "htr"
    solved = "solved"
    leave_slice = "leave slice"

    def __str__(self) -> str:
        return self.value


BEAM_PLANS: Final[dict[PlanName, BeamPlan]] = {
    PlanName.dr: DR_PLAN,
    PlanName.htr: HTR_PLAN,
    PlanName.solved: SOLVED_PLAN,
    PlanName.leave_slice: LEAVE_SLICE_PLAN,
}
