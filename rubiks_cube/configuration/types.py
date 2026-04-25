from __future__ import annotations

import enum
from typing import Callable
from typing import TypeAlias

import numpy as np
import numpy.typing as npt

# Arrays representing masks, patterns, and permutations
MaskArray: TypeAlias = npt.NDArray[np.bool_]
PatternArray: TypeAlias = npt.NDArray[np.uint]
StringArray: TypeAlias = npt.NDArray[np.str_]
IndexArray: TypeAlias = npt.NDArray[np.int_]
PermutationArray: TypeAlias = npt.NDArray[np.uint]
BoolArray: TypeAlias = npt.NDArray[np.bool_]

PermutationValidator: TypeAlias = Callable[[PermutationArray], bool]


class PermutationClassification(enum.Enum):
    BASE = "BASE"
    IDENTITY = "IDENTITY"
    ROTATION = "ROTATION"
