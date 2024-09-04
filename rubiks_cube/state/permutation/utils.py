import numpy as np

from rubiks_cube.utils.types import CubeState


def rotate_face(permutation: CubeState, face: slice, k: int) -> CubeState:
    """Rotate the face 90 degrees counterclock wise."""

    sqrt = np.sqrt(permutation[face].size).astype("int")

    return np.rot90(permutation[face].reshape((sqrt, sqrt)), k).flatten()


def invert(permutation: CubeState) -> CubeState:
    """Return the inverse permutation."""

    inv_permutation = np.empty_like(permutation)
    inv_permutation[permutation] = np.arange(permutation.size)
    return inv_permutation


def multiply(permutation: CubeState, factor: int) -> CubeState:
    """Return the permutation applied multiple times."""

    assert isinstance(factor, int) and factor > 0, "invalid factor!"

    mul_permutation = permutation
    for _ in range(factor - 1):
        mul_permutation = mul_permutation[permutation]

    return mul_permutation
