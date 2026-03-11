from __future__ import annotations

import enum
from typing import Callable
from typing import TypeAlias

import numpy as np
import numpy.typing as npt

# Arrays representing masks, patterns, and permutations
CubeMask: TypeAlias = npt.NDArray[np.bool_]
CubePattern: TypeAlias = npt.NDArray[np.uint]
CubePermutation: TypeAlias = npt.NDArray[np.uint]
CubeColor: TypeAlias = npt.NDArray[np.str_]

# Normal arrays
BoolArray: TypeAlias = npt.NDArray[np.bool_]

PermutationValidator: TypeAlias = Callable[[CubePermutation], bool]


class PermutationClassification(enum.Enum):
    BASE = "BASE"
    IDENTITY = "IDENTITY"
    ROTATION = "ROTATION"
