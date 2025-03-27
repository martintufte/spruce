from rubiks_cube.configuration.types import CubeState


def is_permutation(state: CubeState) -> bool:
    """Check if a state is a valid permutation.

    Args:
        state (CubeState): State to check.

    Returns:
        bool: Whether state is a valid permutation.
    """
    return set(state) == set(range(state.size))


def is_mask(state: CubeState) -> bool:
    """Check if a state is a valid mask.

    Args:
        state (CubeState): State to check.

    Returns:
        bool: Whether state is a valid mask.
    """
    return set(state) == {0, 1}
