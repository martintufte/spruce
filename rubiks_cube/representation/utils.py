import numpy as np

from rubiks_cube.configuration.types import CubeMask
from rubiks_cube.configuration.types import CubePermutation
from rubiks_cube.configuration.types import CubeState


def infer_cube_size(state: CubeState) -> int:
    """Infer the cube size from the state.

    Args:
        state (CubeState): Cube state.

    Returns:
        int: Cube size.

    Raises:
        ValueError: If the cube size cannot be inferred.
    """
    for cube_size in range(1, 11):
        if state.size == (6 * cube_size**2):
            return cube_size
    raise ValueError("Cube size cannot be inferred!")


def rotate_face(perm: CubePermutation, face: slice, k: int) -> CubePermutation:
    """Rotate the face 90 degrees counterclock wise.

    Args:
        perm (CubePermutation): Cube state.
        face (slice): A slice of the cube array.
        k (int): Number of quarter-turn rotations.

    Returns:
        CubeState: Rotated cube state.
    """
    sqrt = np.sqrt(perm[face].size).astype("int")

    return np.rot90(perm[face].reshape((sqrt, sqrt)), k).flatten()


def invert(perm: CubePermutation) -> CubePermutation:
    """Return the inverse permutation.

    Args:
        perm (CubePermutation): Cube state.

    Returns:
        CubePermutation: Inverse state by inverting the permutation.
    """
    inv_perm = np.empty_like(perm)
    inv_perm[perm] = np.arange(perm.size)
    return inv_perm


def multiply(perm: CubePermutation, factor: int) -> CubePermutation:
    """Return the permutation applied multiple times.

    Args:
        perm (CubePermutation): Cube permutation.
        factor (int): Factor to multiply the permutation.

    Returns:
        CubePermutation: Multiplied permutation.
    """
    assert isinstance(factor, int) and factor > 0, "invalid factor!"

    mul_perm = perm
    for _ in range(factor - 1):
        mul_perm = mul_perm[perm]

    return mul_perm


def reindex(perm: CubePermutation, mask: CubeMask) -> CubePermutation:
    """Use the mask to reindex the permutation.

    Note:
        Assumes that perm[~mask] == id[~mask].

    Args:
        perm (CubePermutation): Initial permutation(s).
        mask (CubeMask): Boolean mask.

    Returns:
        CubePermutation: Reindexed permutation.
    """
    new_perm = perm[mask]
    for new_index, index in enumerate(np.where(mask)[0]):
        new_perm[new_perm == index] = new_index

    return new_perm
