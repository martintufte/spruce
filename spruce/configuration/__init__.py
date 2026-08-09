from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Final
from typing import Literal

import attrs

from spruce.configuration.enumeration import Metric
from spruce.configuration.enumeration import Puzzle
from spruce.types import move_symbols

if TYPE_CHECKING:
    from spruce.types import MoveSymbol

DEFAULT_GENERATOR_MAP: Final[dict[Puzzle, frozenset[MoveSymbol]]] = {
    Puzzle._2x2x2: move_symbols("U", "R", "F"),
    Puzzle._3x3x3: move_symbols("U", "D", "L", "R", "F", "B"),
    Puzzle._4x4x4: move_symbols("U", "Uw", "D", "L", "R", "Rw", "F", "Fw", "B"),
}

type LogLevel = Literal["debug", "info", "warning", "error", "critical"]


@attrs.frozen()
class AppConfig:
    puzzle: Puzzle = Puzzle._3x3x3
    metric: Metric = Metric.HTM
    layout: Literal["centered", "wide"] = "centered"
    log_level: LogLevel = "debug"


APP_CFG: Final[AppConfig] = AppConfig()
