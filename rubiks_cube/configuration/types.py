from typing import TypeAlias

import numpy as np
import numpy.typing as npt

# Arrays representing Rubik's cube masks, patterns, and permutations
CubeMask: TypeAlias = npt.NDArray[np.bool_]
CubePattern: TypeAlias = npt.NDArray[np.int_]
CubePermutation: TypeAlias = npt.NDArray[np.int_]
CubeState: TypeAlias = CubeMask | CubePattern | CubePermutation

# Range of cube sizes
CubeRange: TypeAlias = tuple[int | None, int | None]
