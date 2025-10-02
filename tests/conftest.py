from typing import TypeGuard

from rubiks_cube.configuration.types import CubeMask
from rubiks_cube.configuration.types import CubePermutation
from rubiks_cube.configuration.types import CubeState


def is_permutation(state: CubeState) -> TypeGuard[CubePermutation]:
    """Check if a state is a valid permutation.

    Args:
        state (CubeState): State to check.

    Returns:
        bool: Whether state is a valid permutation.
    """
    return set(state) == set(range(state.size))


def is_mask(state: CubeState) -> TypeGuard[CubeMask]:
    """Check if a state is a valid mask.

    Args:
        state (CubeState): State to check.

    Returns:
        bool: Whether state is a valid mask.
    """
    return set(state) == {0, 1}
