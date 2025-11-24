from __future__ import annotations

from typing import Final

from rubiks_cube.configuration.enumeration import Metric

CUBE_SIZE: Final[int] = 3
DEFAULT_METRIC: Final[Metric] = Metric.HTM
DEFAULT_GENERATOR: Final[str] = "<U, D, L, R, F, B>"

LOG_LEVEL: str = "debug"
