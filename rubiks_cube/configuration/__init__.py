from __future__ import annotations

from typing import Final
from typing import Literal

from rubiks_cube.configuration.enumeration import Metric

CUBE_SIZE: Final[int] = 3
METRIC: Final[Metric] = Metric.HTM
APP_MODE: Final[Literal["development", "production"]] = "development"
