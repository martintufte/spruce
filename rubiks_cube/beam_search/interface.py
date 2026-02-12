from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Literal
from typing import Mapping
from typing import Sequence
from typing import TypeAlias

import attrs

if TYPE_CHECKING:
    from rubiks_cube.configuration.enumeration import Goal
    from rubiks_cube.move.generator import MoveGenerator

SideMode: TypeAlias = Literal["same", "switch", "both", "normal", "inverse"]


@attrs.frozen
class Transition:
    allowed_prev_goals: dict[Goal, list[Goal]] | None = None
    generator_by_prev_goal: dict[Goal, MoveGenerator] | None = None
    side_mode: SideMode = "same"

    def allowed_prev_goals_for(self, goal: Goal) -> list[Goal] | None:
        if self.allowed_prev_goals is None:
            return None
        return self.allowed_prev_goals.get(goal)

    def generator_for_prev_goal(
        self, prev_goal: Goal | None, fallback: MoveGenerator | None
    ) -> MoveGenerator | None:
        if prev_goal is None or self.generator_by_prev_goal is None:
            return fallback
        return self.generator_by_prev_goal.get(prev_goal, fallback)


@attrs.frozen
class BeamStep:
    goals: list[Goal]
    subset_filters: dict[Goal, list[str]] | list[str] | None = None
    transition: Transition | None = None
    generator: MoveGenerator | None = None
    min_search_depth: int = 0
    max_search_depth: int = 10
    max_solutions: int = 1
    max_time: float | None = None

    def allowed_subsets(self, goal: Goal) -> list[str] | None:
        if self.subset_filters is None:
            return None
        if not self.subset_filters:
            raise ValueError("BeamStep subset_filters cannot be empty.")
        if isinstance(self.subset_filters, Mapping):
            allowed = self.subset_filters.get(goal)
            if allowed is None:
                return None
            return list(allowed)
        return list(self.subset_filters)


@attrs.frozen
class BeamPlan:
    name: str | None
    steps: list[BeamStep]

    @classmethod
    def from_steps(cls, steps: Sequence[BeamStep], name: str | None = None) -> BeamPlan:
        return cls(name=name, steps=list(steps))
