from __future__ import annotations

import enum
from collections.abc import Callable

import numpy as np
import numpy.typing as npt

type MaskArray = npt.NDArray[np.bool_]
type PatternArray = npt.NDArray[np.uint]
type StringArray = npt.NDArray[np.str_]
type IndexArray = npt.NDArray[np.int_]
type PermutationArray = npt.NDArray[np.uint]
type BoolArray = npt.NDArray[np.bool_]

type PermutationValidator = Callable[[PermutationArray], bool]


class PermutationClassification(enum.Enum):
    BASE = "BASE"
    IDENTITY = "IDENTITY"
    ROTATION = "ROTATION"
