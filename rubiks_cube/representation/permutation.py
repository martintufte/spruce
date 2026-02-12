from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING

import numpy as np

from rubiks_cube.configuration import CUBE_SIZE
from rubiks_cube.representation.utils import invert
from rubiks_cube.representation.utils import multiply
from rubiks_cube.representation.utils import rotate_face

if TYPE_CHECKING:
    from rubiks_cube.configuration.types import CubePermutation
    from rubiks_cube.move.sequence import MoveSequence


def get_identity_permutation(cube_size: int = CUBE_SIZE) -> CubePermutation:
    """Return the identity permutation of the cube.

    Args:
        cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.

    Returns:
        CubePermutation: Identity permutation.
    """

    return np.arange(6 * cube_size**2, dtype=int)


@lru_cache(maxsize=10)
def create_permutations(cube_size: int = CUBE_SIZE) -> dict[str, CubePermutation]:
    """Return a dictionaty over all legal turns.

    Args:
        cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.

    Returns:
        dict[str, CubePermutation]: Dictionary of all permutations.
    """
    assert 1 <= cube_size <= 10, "Size must be between 1 and 10."

    # Define identity
    identity = get_identity_permutation(cube_size=cube_size)

    # Define faces
    face_size = cube_size**2
    up = slice(0, face_size)
    front = slice(face_size, 2 * face_size)
    right = slice(2 * face_size, 3 * face_size)
    back = slice(3 * face_size, 4 * face_size)
    left = slice(4 * face_size, 5 * face_size)
    down = slice(5 * face_size, 6 * face_size)

    # Define rotation x
    x = np.copy(identity)
    x[up] = identity[front]
    x[front] = identity[down]
    x[right] = rotate_face(identity, right, -1)
    x[back] = rotate_face(identity, up, 2)
    x[left] = rotate_face(identity, left, 1)
    x[down] = rotate_face(identity, back, 2)

    # Define rotation y
    y = np.copy(identity)
    y[up] = rotate_face(identity, up, -1)
    y[front] = identity[right]
    y[right] = identity[back]
    y[back] = identity[left]
    y[left] = identity[front]
    y[down] = rotate_face(identity, down, 1)

    # Define up face rotations (U, Uw, 3Uw, ... (n-1)Uw)
    us = []
    for i in range(1, cube_size):
        u = np.copy(identity)
        affected = slice(0, i * cube_size)
        u[up] = rotate_face(identity, up, -1)
        u[front][affected] = identity[right][affected]
        u[right][affected] = identity[back][affected]
        u[back][affected] = identity[left][affected]
        u[left][affected] = identity[front][affected]
        us.append(u)

    return_dict = get_permutation_dictionary(
        identity=identity,
        x=x,
        y=y,
        us=us,
        cube_size=cube_size,
    )
    return return_dict


def get_permutation_dictionary(
    identity: CubePermutation,
    x: CubePermutation,
    y: CubePermutation,
    us: list[CubePermutation],
    cube_size: int = CUBE_SIZE,
) -> dict[str, CubePermutation]:
    """Define all other permutations from identity, x, y and us moves.

    Args:
        identity (CubePermutation): Identity permutation.
        x (CubePermutation): Rotation x.
        y (CubePermutation): Rotation y.
        us (list[CubePermutation]): Up face rotations.
        cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.

    Returns:
        dict[str, CubePermutation]: Dictionary of all permutations.
    """
    # Rotations with doubles and inverses
    # x rotation given
    x2 = multiply(x, 2)
    xi = invert(x)
    # y rotation given
    y2 = multiply(y, 2)
    yi = invert(y)
    z = identity[x][y][xi]
    z2 = multiply(z, 2)
    zi = invert(z)

    # Face turns with inverses and doubles
    # U moves given
    fs = [identity[x][u][xi] for u in us]
    rs = [identity[zi][u][z] for u in us]
    bs = [identity[xi][u][x] for u in us]
    ls = [identity[z][u][zi] for u in us]
    ds = [identity[x2][u][x2] for u in us]

    us_inv = [invert(p) for p in us]
    fs_inv = [invert(p) for p in fs]
    rs_inv = [invert(p) for p in rs]
    bs_inv = [invert(p) for p in bs]
    ls_inv = [invert(p) for p in ls]
    ds_inv = [invert(p) for p in ds]

    us_double = [multiply(p, 2) for p in us]
    fs_double = [multiply(p, 2) for p in fs]
    rs_double = [multiply(p, 2) for p in rs]
    bs_double = [multiply(p, 2) for p in bs]
    ls_double = [multiply(p, 2) for p in ls]
    ds_double = [multiply(p, 2) for p in ds]

    # Identity and rotations
    return_dict = {
        "I": identity,
        "x": x,
        "x2": x2,
        "x'": xi,
        "y": y,
        "y2": y2,
        "y'": yi,
        "z": z,
        "z2": z2,
        "z'": zi,
    }

    # Slice turns for 3x3 and higher
    if cube_size > 2:
        m = identity[rs[0]][rs_inv[-1]]
        m2 = multiply(m, 2)
        mi = invert(m)
        s = identity[fs[-1]][fs_inv[0]]
        s2 = multiply(s, 2)
        si = invert(s)
        e = identity[us[0]][us_inv[-1]]
        e2 = multiply(e, 2)
        ei = invert(e)
        return_dict.update(
            {
                "M": m,
                "M2": m2,
                "M'": mi,
                "S": s,
                "S2": s2,
                "S'": si,
                "E": e,
                "E2": e2,
                "E'": ei,
            }
        )

    # Inner slice turns for 4x4
    if cube_size == 4:
        r = identity[rs[1]][rs_inv[0]]
        r2 = multiply(r, 2)
        ri = invert(r)
        el = identity[ls[1]][ls_inv[0]]
        l2 = multiply(el, 2)
        li = invert(el)
        return_dict.update({"r": r, "r2": r2, "r'": ri, "l": el, "l2": l2, "l'": li})

    # Face turns
    for i, (p, pi, p2) in enumerate(zip(us, us_inv, us_double, strict=False), start=1):
        base_str = str(i) + "Uw" if i > 2 else "Uw" if i == 2 else "U"
        return_dict.update({base_str: p, base_str + "'": pi, base_str + "2": p2})
    for i, (p, pi, p2) in enumerate(zip(fs, fs_inv, fs_double, strict=False), start=1):
        base_str = str(i) + "Fw" if i > 2 else "Fw" if i == 2 else "F"
        return_dict.update({base_str: p, base_str + "'": pi, base_str + "2": p2})
    for i, (p, pi, p2) in enumerate(zip(rs, rs_inv, rs_double, strict=False), start=1):
        base_str = str(i) + "Rw" if i > 2 else "Rw" if i == 2 else "R"
        return_dict.update({base_str: p, base_str + "'": pi, base_str + "2": p2})
    for i, (p, pi, p2) in enumerate(zip(bs, bs_inv, bs_double, strict=False), start=1):
        base_str = str(i) + "Bw" if i > 2 else "Bw" if i == 2 else "B"
        return_dict.update({base_str: p, base_str + "'": pi, base_str + "2": p2})
    for i, (p, pi, p2) in enumerate(zip(ls, ls_inv, ls_double, strict=False), start=1):
        base_str = str(i) + "Lw" if i > 2 else "Lw" if i == 2 else "L"
        return_dict.update({base_str: p, base_str + "'": pi, base_str + "2": p2})
    for i, (p, pi, p2) in enumerate(zip(ds, ds_inv, ds_double, strict=False), start=1):
        base_str = str(i) + "Dw" if i > 2 else "Dw" if i == 2 else "D"
        return_dict.update({base_str: p, base_str + "'": pi, base_str + "2": p2})

    return return_dict


def apply_moves_to_permutation(
    permutation: CubePermutation, sequence: MoveSequence, cube_size: int = CUBE_SIZE
) -> CubePermutation:
    """Apply a sequence of moves to the permutation.

    Args:
        permutation (CubePermutation): Rubik's cube permutation.
        sequence (MoveSequence): Sequence of moves.
        cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.

    Returns:
        CubePermutation: Permutation after applying the moves.
    """
    permutations = create_permutations(cube_size=cube_size)

    for move in sequence:
        permutation = permutation[permutations[move]]

    return permutation
