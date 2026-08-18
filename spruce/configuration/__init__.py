from __future__ import annotations

from typing import Final
from typing import Literal

import attrs

from spruce.puzzle.cube.metrics import Metric
from spruce.puzzle.cube.spec import Puzzle

type LogLevel = Literal["debug", "info", "warning", "error", "critical"]


@attrs.frozen()
class AppConfig:
    puzzle: Puzzle = Puzzle._3x3x3
    metric: Metric = Metric.HTM
    layout: Literal["centered", "wide"] = "centered"
    log_level: LogLevel = "debug"


APP_CFG: Final[AppConfig] = AppConfig()
