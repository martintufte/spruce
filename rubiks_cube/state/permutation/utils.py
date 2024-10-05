import numpy as np

from rubiks_cube.configuration.type_definitions import CubeState


def rotate_face(state: CubeState, face: slice, k: int) -> CubeState:
    """Rotate the face 90 degrees counterclock wise.

    Args:
        state (CubeState): Cube state.
        face (slice): A slice of the cube array.
        k (int): Number of quarter-turn rotations.

    Returns:
        CubeState: Rotated cube state.
    """

    sqrt = np.sqrt(state[face].size).astype("int")

    return np.rot90(state[face].reshape((sqrt, sqrt)), k).flatten()


def invert(state: CubeState) -> CubeState:
    """Return the inverse permutation.

    Args:
        state (CubeState): Cube state.

    Returns:
        CubeState: Inverse state by inverting the permutation.
    """

    inv_state = np.empty_like(state)
    inv_state[state] = np.arange(state.size)
    return inv_state


def multiply(state: CubeState, factor: int) -> CubeState:
    """Return the permutation applied multiple times.

    Args:
        state (CubeState): Cube state.
        factor (int): Factor to multiply the permutation.

    Returns:
        CubeState: Multiplied permutation.
    """

    assert isinstance(factor, int) and factor > 0, "invalid factor!"

    mul_state = state
    for _ in range(factor - 1):
        mul_state = mul_state[state]

    return mul_state
