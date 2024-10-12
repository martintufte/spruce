from typing import Any
from typing import TypeAlias

import numpy as np
import numpy.typing as npt

# Permutation of the cubies
CubePermutation: TypeAlias = npt.NDArray[np.int_]

# Boolean mask of the cubies
CubeMask: TypeAlias = npt.NDArray[np.bool_]

# General state of the Rubik's cube
CubeState: TypeAlias = npt.NDArray[Any]
