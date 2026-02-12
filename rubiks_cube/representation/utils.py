from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from rubiks_cube.configuration.types import CubeMask
    from rubiks_cube.configuration.types import CubePermutation


def rotate_face(permutation: CubePermutation, face: slice, k: int) -> CubePermutation:
    """Rotate the face 90 degrees counterclock wise.

    Args:
        permutation (CubePermutation): Cube permutation.
        face (slice): A slice of the cube array.
        k (int): Number of quarter-turn rotations.

    Returns:
        CubePermutation: Rotated cube permutation.
    """
    sqrt = np.sqrt(permutation[face].size).astype("int")

    return np.rot90(permutation[face].reshape((sqrt, sqrt)), k).flatten()


def invert(permutation: CubePermutation) -> CubePermutation:
    """Return the inverse permutation.

    Args:
        perm (CubePermutation): Cube permutation.

    Returns:
        CubePermutation: Inverse permutation.
    """
    inv_permutation = np.empty_like(permutation)
    inv_permutation[permutation] = np.arange(permutation.size)
    return inv_permutation


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
