from __future__ import annotations

from typing import Final
from typing import Literal
from typing import TypeAlias

import attrs

from rubiks_cube.configuration.enumeration import Metric

DEFAULT_METRIC: Final[Metric] = Metric.HTM

DEFAULT_GENERATOR_MAP: Final[dict[int, str]] = {
    2: "<U, R, F>",
    3: "<U, D, L, R, F, B>",
    4: "<U, Uw, D, L, R, Rw, F, Fw, B>",
}

LogLevel: TypeAlias = Literal["debug", "info", "warning", "error", "critical"]


@attrs.frozen()
class AppConfig:
    cube_size: int = 4
    metric: Metric = Metric.HTM
    layout: Literal["centered", "wide"] = "centered"
    log_level: LogLevel = "debug"


APP_CFG: Final[AppConfig] = AppConfig()
