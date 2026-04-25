from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from rubiks_cube.configuration.types import MaskArray
    from rubiks_cube.configuration.types import PermutationArray


def get_identity(size: int) -> PermutationArray:
    """Return the identity permutation of the cube.

    Args:
        size (int): Size of the permutation.

    Returns:
        PermutationArray: Identity permutation.
    """

    return np.arange(size, dtype=np.uint)


def invert(permutation: PermutationArray) -> PermutationArray:
    """Return the inverse permutation.

    Args:
        perm (PermutationArray): Cube permutation.

    Returns:
        PermutationArray: Inverse permutation.
    """
    inv_permutation = np.empty_like(permutation)
    inv_permutation[permutation] = np.arange(permutation.size)
    return inv_permutation


def multiply(base: PermutationArray, factor: int) -> PermutationArray:
    """Return the permutation applied multiple times.

    Args:
        base (PermutationArray): Base permutation.
        factor (int): Factor to multiply the permutation.

    Returns:
        PermutationArray: Multiplied permutation.
    """
    assert isinstance(factor, int) and factor >= 0, "invalid factor!"

    result = np.arange(base.size, dtype=np.uint)
    while factor > 0:
        if factor & 1:
            result = result[base]
        base = base[base]
        factor >>= 1

    return result


def conjugate(perm: PermutationArray, g: PermutationArray) -> PermutationArray:
    """Return the conjugate of a permutation by g.

    Uses the project's permutation composition convention:
        conjugate(perm, g) = g * perm * g^-1

    Args:
        perm (PermutationArray): Permutation to conjugate.
        g (PermutationArray): Conjugating permutation.

    Returns:
        PermutationArray: Conjugated permutation.
    """
    return g[perm][invert(g)]


def reindex(perm: PermutationArray, mask: MaskArray) -> PermutationArray:
    """Use the mask to reindex the permutation.

    Args:
        perm (PermutationArray): Initial permutation(s).
        mask (MaskArray): Boolean mask.

    Returns:
        PermutationArray: Reindexed permutation.

    Note:
        Requires that masked and unmasked indices each form a closed orbit under
        perm. Unmasked positions may permute freely among themselves.
    """
    new_perm = perm[mask]
    for new_index, index in enumerate(np.where(mask)[0]):
        new_perm[new_perm == index] = new_index

    return new_perm
