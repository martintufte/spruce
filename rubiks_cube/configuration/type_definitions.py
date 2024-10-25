from typing import Any
from typing import TypeAlias

import numpy as np
import numpy.typing as npt

# Rubik's cube states
CubeState: TypeAlias = npt.NDArray[Any]
CubePattern: TypeAlias = npt.NDArray[np.int_]
CubePermutation: TypeAlias = npt.NDArray[np.int_]
CubeMask: TypeAlias = npt.NDArray[np.bool_]

# Range of cube sizes
CubeRange: TypeAlias = tuple[int | None, int | None]
