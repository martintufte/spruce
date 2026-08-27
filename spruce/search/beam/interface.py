from __future__ import annotations

from enum import Enum
from typing import Final

import attrs

from spruce.types import GoalId
from spruce.types import MoveSymbol
from spruce.types import PatternArray
from spruce.types import PermutationValidator
from spruce.types import VariantId


class SearchSideChoice(Enum):
    """Which search side(s) to use for a beam step, relative to the incoming candidate."""

    prev = "prev"
    normal = "normal"
    inverse = "inverse"
    switch = "switch"
    both = "both"

    def __str__(self) -> str:
        return self.value


@attrs.frozen
class Transition:
    """Configuration for how a beam step transitions from the previous step.

    ``generator_map`` has dual semantics depending on step position:

    - **First step** (no predecessor): the key must be ``NO_VARIANT``, and the
      value is the set of move symbols generating the search's action space.
    - **Subsequent steps**: each key is a *previous step's variant* (resolved via
      ``prev_goal_ref``), and the value is the set of move symbols allowed when arriving
      from that variant. ``prev_goal_ref`` is a negative index into the candidate's
      variant history (-1 = last, -2 = second-to-last, etc.).
    """

    search_side: SearchSideChoice = SearchSideChoice.prev
    generator_map: dict[VariantId, frozenset[MoveSymbol]] = attrs.field(factory=dict)
    allowed_variants_by_prev_variant: dict[VariantId, frozenset[VariantId]] | None = None
    prev_goal_ref: int = -1
    check_contained: bool = False

    def __attrs_post_init__(self) -> None:
        if not self.generator_map:
            raise ValueError("Transition.generator_map must be non-empty")


@attrs.frozen
class BeamStep:
    goal: GoalId
    variants: list[VariantId]
    transition: Transition
    max_search_depth: int = 10
    max_solutions: int = 1


@attrs.frozen
class BeamPlan:
    name: str
    steps: tuple[BeamStep, ...]


@attrs.frozen
class GoalPatterns:
    """The patterns a goal accepts, one per variant, plus any extra predicate."""

    variants: dict[VariantId, PatternArray]
    validator: PermutationValidator | None = None

    def __getitem__(self, variant: VariantId) -> PatternArray:
        return self.variants[variant]


# The history of a candidate that has not solved anything yet.
NO_GOAL: Final[GoalId] = GoalId("none")
NO_VARIANT: Final[VariantId] = VariantId("none")
