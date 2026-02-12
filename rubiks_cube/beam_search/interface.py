from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Literal
from typing import TypeAlias

import attrs

if TYPE_CHECKING:
    from rubiks_cube.configuration.enumeration import Goal
    from rubiks_cube.move.generator import MoveGenerator

SideMode: TypeAlias = Literal["same", "switch", "both", "normal", "inverse"]


@attrs.frozen
class Transition:
    prev_goal_contained: bool = False
    generator_by_prev_goal: dict[Goal, MoveGenerator] | None = None
    side_mode: SideMode = "same"

    def generator_for_prev_goal(
        self, prev_goal: Goal | None, fallback: MoveGenerator | None
    ) -> MoveGenerator | None:
        if prev_goal is None or self.generator_by_prev_goal is None:
            return fallback
        return self.generator_by_prev_goal.get(prev_goal, fallback)


@attrs.frozen
class BeamStep:
    goals: list[Goal]
    transition: Transition | None = None
    generator: MoveGenerator | None = None
    min_search_depth: int = 0
    max_search_depth: int = 10
    max_solutions: int = 1
    max_time: float | None = None


@attrs.frozen
class BeamPlan:
    name: str
    steps: list[BeamStep]
