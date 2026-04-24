from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

import attrs

if TYPE_CHECKING:
    from rubiks_cube.configuration.enumeration import Goal
    from rubiks_cube.configuration.enumeration import Variant
    from rubiks_cube.move.generator import MoveGenerator


class SearchSideChoice(Enum):
    """Which search side(s) to use for a beam step, relative to the incoming candidate."""

    prev = "prev"
    normal = "normal"
    inverse = "inverse"
    switch = "switch"
    both = "both"

    def __str__(self) -> str:
        return self.value


class PrevGoalRef(Enum):
    """Which entry in a candidate's variant history acts as the generator-map key.

    ``last`` (-1) selects the most recent variant; ``second_last`` (-2) reaches one
    step further back, useful for steps that need context from two levels up.
    """

    last = -1
    second_last = -2

    def __str__(self) -> str:
        return self.name


@attrs.frozen
class Transition:
    """Configuration for how a beam step transitions from the previous step.

    ``generator_map`` has dual semantics depending on step position:

    - **First step** (no predecessor): the key must be ``Variant.none``, and the
      value is the source move generator for the search.
    - **Subsequent steps**: each key is a *previous step's variant* (resolved via
      ``prev_goal_ref``), and the value is the move generator allowed when arriving
      from that variant.
    """

    search_side: SearchSideChoice = SearchSideChoice.prev
    generator_map: dict[Variant, MoveGenerator] = attrs.field(factory=dict)
    allowed_variants_by_prev_variant: dict[Variant, frozenset[Variant]] | None = None
    prev_goal_ref: PrevGoalRef = PrevGoalRef.last
    check_contained: bool = False

    def __attrs_post_init__(self) -> None:
        if not self.generator_map:
            raise ValueError("Transition.generator_map must be non-empty")


@attrs.frozen
class BeamStep:
    goal: Goal
    variants: list[Variant]
    transition: Transition
    max_search_depth: int = 10
    max_solutions: int = 1


@attrs.frozen
class BeamPlan:
    name: str
    cube_size: int
    steps: tuple[BeamStep, ...]
