from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Literal

import attrs

if TYPE_CHECKING:
    from rubiks_cube.configuration.enumeration import Goal
    from rubiks_cube.configuration.enumeration import Variant
    from rubiks_cube.move.generator import MoveGenerator


@attrs.frozen
class Transition:
    search_side: Literal["prev", "switch", "both", "normal", "inverse"] = "prev"
    generator_map: dict[Variant, MoveGenerator] = attrs.field(factory=dict)
    allowed_variants_by_prev_variant: dict[Variant, frozenset[Variant]] | None = None
    prev_goal_index: int = -1
    check_contained: bool = False


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
    steps: list[BeamStep]
