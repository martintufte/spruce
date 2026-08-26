from __future__ import annotations

from enum import Enum
from typing import Final

import attrs

from spruce.puzzle.cube.goals import Goal
from spruce.puzzle.cube.spec import Puzzle
from spruce.puzzle.cube.variants import Variant
from spruce.search.beam.interface import BeamPlan
from spruce.search.beam.interface import BeamStep
from spruce.search.beam.interface import SearchSideChoice
from spruce.search.beam.interface import Transition
from spruce.types import GoalId
from spruce.types import MoveSymbol
from spruce.types import VariantId


def _goal(goal: Goal) -> GoalId:
    """Label a beam step with a goal; the search only ever compares these as strings."""
    return GoalId(goal.value)


def _variant(variant: Variant) -> VariantId:
    """Label a beam step's variant; the search only ever compares these as strings."""
    return VariantId(variant.value)


def _symbols(*symbols: str) -> frozenset[MoveSymbol]:
    """Build a generator without validation; `build_step_contexts` validates each
    generator against the move meta of the plan's own puzzle via `get_actions`."""
    return frozenset(MoveSymbol(symbol) for symbol in symbols)


EO_STEP: Final[BeamStep] = BeamStep(
    goal=_goal(Goal.eo),
    variants=[_variant(Variant.lr), _variant(Variant.fb), _variant(Variant.ud)],
    transition=Transition(
        search_side=SearchSideChoice.both,
        generator_map={
            _variant(Variant.none): _symbols("L", "R", "F", "B", "U", "D"),
        },
    ),
    max_search_depth=6,
    max_solutions=30,
)

DR_STEP: Final[BeamStep] = BeamStep(
    goal=_goal(Goal.dr),
    variants=[_variant(Variant.lr), _variant(Variant.fb), _variant(Variant.ud)],
    transition=Transition(
        search_side=SearchSideChoice.both,
        generator_map={
            _variant(Variant.lr): _symbols("L2", "R2", "F", "B", "U", "D"),
            _variant(Variant.fb): _symbols("L", "R", "F2", "B2", "U", "D"),
            _variant(Variant.ud): _symbols("L", "R", "F", "B", "U2", "D2"),
        },
        check_contained=True,
    ),
    max_search_depth=10,
    max_solutions=10,
)

HTR_STEP: Final[BeamStep] = BeamStep(
    goal=_goal(Goal.htr),
    variants=[_variant(Variant.none)],
    transition=Transition(
        search_side=SearchSideChoice.both,
        generator_map={
            _variant(Variant.lr): _symbols("L", "R", "F2", "B2", "U2", "D2"),
            _variant(Variant.fb): _symbols("L2", "R2", "F", "B", "U2", "D2"),
            _variant(Variant.ud): _symbols("L2", "R2", "F2", "B2", "U", "D"),
        },
    ),
    max_search_depth=12,
    max_solutions=10,
)

FINISH_STEP: Final[BeamStep] = BeamStep(
    goal=_goal(Goal.solved),
    variants=[_variant(Variant.none)],
    transition=Transition(
        search_side=SearchSideChoice.prev,
        generator_map={
            _variant(Variant.none): _symbols("L2", "R2", "F2", "B2", "U2", "D2"),
        },
    ),
    max_search_depth=12,
    max_solutions=5,
)

LEAVE_SLICE_STEP: Final[BeamStep] = BeamStep(
    goal=_goal(Goal.leave_slice),
    variants=[_variant(Variant.lr), _variant(Variant.fb), _variant(Variant.ud)],
    transition=Transition(
        search_side=SearchSideChoice.prev,
        generator_map={
            _variant(Variant.none): _symbols("L2", "R2", "F2", "B2", "U2", "D2"),
        },
    ),
    max_search_depth=10,
    max_solutions=10,
)

DR_PLAN: Final[BeamPlan] = BeamPlan(
    name="dr",
    steps=(EO_STEP, DR_STEP),
)

HTR_PLAN: Final[BeamPlan] = BeamPlan(
    name="htr",
    steps=(EO_STEP, DR_STEP, HTR_STEP),
)

SOLVED_PLAN: Final[BeamPlan] = BeamPlan(
    name="solved",
    steps=(EO_STEP, DR_STEP, HTR_STEP, FINISH_STEP),
)

LEAVE_SLICE_PLAN: Final[BeamPlan] = BeamPlan(
    name="leave slice",
    steps=(EO_STEP, DR_STEP, HTR_STEP, FINISH_STEP, LEAVE_SLICE_STEP),
)


@attrs.frozen
class CubePlan:
    """A beam plan together with the cube it was written for."""

    plan: BeamPlan
    puzzle: Puzzle


class PlanName(Enum):
    dr = "dr"
    htr = "htr"
    solved = "solved"
    leave_slice = "leave slice"

    def __str__(self) -> str:
        return self.value


BEAM_PLANS: Final[dict[PlanName, CubePlan]] = {
    PlanName.dr: CubePlan(plan=DR_PLAN, puzzle=Puzzle._3x3x3),
    PlanName.htr: CubePlan(plan=HTR_PLAN, puzzle=Puzzle._3x3x3),
    PlanName.solved: CubePlan(plan=SOLVED_PLAN, puzzle=Puzzle._3x3x3),
    PlanName.leave_slice: CubePlan(plan=LEAVE_SLICE_PLAN, puzzle=Puzzle._3x3x3),
}
