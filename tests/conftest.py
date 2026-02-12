from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any
from typing import TypeGuard

if TYPE_CHECKING:
    import numpy.typing as npt

    from rubiks_cube.configuration.types import CubePermutation


def is_permutation(state: npt.NDArray[Any]) -> TypeGuard[CubePermutation]:
    """Check if a state is a valid permutation.

    Args:
        state (CubePermutation): Permutation to check.

    Returns:
        bool: Whether state is a valid permutation.
    """
    return set(state) == set(range(state.size))
