from __future__ import annotations

from typing import Final

from rubiks_cube.configuration.enumeration import Metric

CUBE_SIZE: Final[int] = 3
METRIC: Final[Metric] = Metric.HTM
DEFAULT_GENERATOR: Final[str] = "<L, R, F, B, U, D>"

LOG_LEVEL: str = "debug"
