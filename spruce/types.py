from __future__ import annotations

from collections.abc import Callable
from typing import NewType

import numpy as np
import numpy.typing as npt

type MaskArray = npt.NDArray[np.bool_]
type PatternArray = npt.NDArray[np.uint]
type StringArray = npt.NDArray[np.str_]
type IndexArray = npt.NDArray[np.int_]
type PermutationArray = npt.NDArray[np.uint]
type BoolArray = npt.NDArray[np.bool_]

type PermutationValidator = Callable[[PermutationArray], bool]


MoveSymbol = NewType("MoveSymbol", str)

# Labels for a search target and one of its symmetric variants. Opaque to the search
# layer: a puzzle chooses the strings, and the search only ever compares them.
GoalId = NewType("GoalId", str)
VariantId = NewType("VariantId", str)
