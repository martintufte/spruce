from __future__ import annotations

from typing import Final
from typing import Literal

import attrs

from spruce.configuration.enumeration import Metric
from spruce.configuration.enumeration import Puzzle

DEFAULT_GENERATOR_MAP: Final[dict[Puzzle, frozenset[str]]] = {
    Puzzle._2x2x2: frozenset({"U", "R", "F"}),
    Puzzle._3x3x3: frozenset({"U", "D", "L", "R", "F", "B"}),
    Puzzle._4x4x4: frozenset({"U", "Uw", "D", "L", "R", "Rw", "F", "Fw", "B"}),
}

type LogLevel = Literal["debug", "info", "warning", "error", "critical"]


@attrs.frozen()
class AppConfig:
    puzzle: Puzzle = Puzzle._3x3x3
    metric: Metric = Metric.HTM
    layout: Literal["centered", "wide"] = "centered"
    log_level: LogLevel = "debug"


APP_CFG: Final[AppConfig] = AppConfig()
