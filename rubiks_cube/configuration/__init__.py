from typing import Final
from typing import Literal

from rubiks_cube.configuration.enumeration import Metric

CUBE_SIZE: Final[int] = 3
METRIC: Final[Metric] = Metric.HTM
ATTEMPT_TYPE: Final[Literal["fewest_moves", "speedsolve"]] = "speedsolve"
APP_MODE: Final[Literal["development", "production"]] = "development"
