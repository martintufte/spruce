from __future__ import annotations

from enum import Enum

import attrs

from spruce.puzzle.cube.goals import Goal  # noqa: TC001
from spruce.puzzle.cube.spec import Puzzle  # noqa: TC001
from spruce.puzzle.cube.variants import Variant  # noqa: TC001
from spruce.types import MoveSymbol  # noqa: TC001


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

    - **First step** (no predecessor): the key must be ``Variant.none``, and the
      value is the set of move symbols generating the search's action space.
    - **Subsequent steps**: each key is a *previous step's variant* (resolved via
      ``prev_goal_ref``), and the value is the set of move symbols allowed when arriving
      from that variant. ``prev_goal_ref`` is a negative index into the candidate's
      variant history (-1 = last, -2 = second-to-last, etc.).
    """

    search_side: SearchSideChoice = SearchSideChoice.prev
    generator_map: dict[Variant, frozenset[MoveSymbol]] = attrs.field(factory=dict)
    allowed_variants_by_prev_variant: dict[Variant, frozenset[Variant]] | None = None
    prev_goal_ref: int = -1
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
    puzzle: Puzzle
    steps: tuple[BeamStep, ...]
