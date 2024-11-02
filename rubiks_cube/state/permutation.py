from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING

import numpy as np

from rubiks_cube.configuration import CUBE_SIZE
from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.state.utils import invert
from rubiks_cube.state.utils import multiply
from rubiks_cube.state.utils import rotate_face

if TYPE_CHECKING:
    from rubiks_cube.configuration.types import CubePermutation


def get_identity_permutation(cube_size: int = CUBE_SIZE) -> CubePermutation:
    """Return the identity permutation of the cube.

    Args:
        cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.

    Returns:
        CubeState: Identity permutation.
    """

    assert 1 <= cube_size <= 10, "Size must be between 1 and 10."

    return np.arange(6 * cube_size**2, dtype=int)


@lru_cache(maxsize=10)
def create_permutations(cube_size: int = CUBE_SIZE) -> dict[str, CubePermutation]:
    """Return a dictionaty over all legal turns.

    Args:
        cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.

    Returns:
        dict[str, CubeState]: Dictionary of all permutations.
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
    Us = []
    for i in range(1, cube_size):
        U = np.copy(identity)
        affected = slice(0, i * cube_size)
        U[up] = rotate_face(identity, up, -1)
        U[front][affected] = identity[right][affected]
        U[right][affected] = identity[back][affected]
        U[back][affected] = identity[left][affected]
        U[left][affected] = identity[front][affected]
        Us.append(U)

    return_dict = get_permutation_dictionary(
        identity=identity,
        x=x,
        y=y,
        Us=Us,
        cube_size=cube_size,
    )
    return return_dict


def get_permutation_dictionary(
    identity: CubePermutation,
    x: CubePermutation,
    y: CubePermutation,
    Us: list[CubePermutation],
    cube_size: int = CUBE_SIZE,
) -> dict[str, CubePermutation]:
    """Define all other permutations from identity, x, y and Us moves.

    Args:
        identity (CubePermutation): Identity permutation.
        x (CubePermutation): Rotation x.
        y (CubePermutation): Rotation y.
        Us (list[CubePermutation]): Up face rotations.
        cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.

    Returns:
        dict[str, CubePermutation]: Dictionary of all permutations.
    """

    # Rotations with doubles and inverses
    # x (defined)
    x2 = multiply(x, 2)
    xi = invert(x)
    # y (defined)
    y2 = multiply(y, 2)
    yi = invert(y)
    z = identity[x][y][xi]
    z2 = multiply(z, 2)
    zi = invert(z)

    # Face turns with inverses and doubles
    # Us (defined)
    Fs = [identity[x][u][xi] for u in Us]
    Rs = [identity[zi][u][z] for u in Us]
    Bs = [identity[xi][u][x] for u in Us]
    Ls = [identity[z][u][zi] for u in Us]
    Ds = [identity[x2][u][x2] for u in Us]

    Us_inv = [invert(p) for p in Us]
    Fs_inv = [invert(p) for p in Fs]
    Rs_inv = [invert(p) for p in Rs]
    Bs_inv = [invert(p) for p in Bs]
    Ls_inv = [invert(p) for p in Ls]
    Ds_inv = [invert(p) for p in Ds]

    Us_double = [multiply(p, 2) for p in Us]
    Fs_double = [multiply(p, 2) for p in Fs]
    Rs_double = [multiply(p, 2) for p in Rs]
    Bs_double = [multiply(p, 2) for p in Bs]
    Ls_double = [multiply(p, 2) for p in Ls]
    Ds_double = [multiply(p, 2) for p in Ds]

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
        M = identity[Rs[0]][Rs_inv[-1]]
        M2 = multiply(M, 2)
        Mi = invert(M)
        S = identity[Fs[-1]][Fs_inv[0]]
        S2 = multiply(S, 2)
        Si = invert(S)
        E = identity[Us[0]][Us_inv[-1]]
        E2 = multiply(E, 2)
        Ei = invert(E)
        return_dict.update(
            {
                "M": M,
                "M2": M2,
                "M'": Mi,
                "S": S,
                "S2": S2,
                "S'": Si,
                "E": E,
                "E2": E2,
                "E'": Ei,
            }
        )

    # Inner slice turns for 4x4
    if cube_size == 4:
        r = identity[Rs[1]][Rs_inv[0]]
        r2 = multiply(r, 2)
        ri = invert(r)
        el = identity[Ls[1]][Ls_inv[0]]
        l2 = multiply(el, 2)
        li = invert(el)
        return_dict.update({"r": r, "r2": r2, "r'": ri, "l": el, "l2": l2, "l'": li})

    # Face turns
    for i, (p, pi, p2) in enumerate(zip(Us, Us_inv, Us_double), start=1):
        base_str = str(i) + "Uw" if i > 2 else "Uw" if i == 2 else "U"
        return_dict.update({base_str: p, base_str + "'": pi, base_str + "2": p2})
    for i, (p, pi, p2) in enumerate(zip(Fs, Fs_inv, Fs_double), start=1):
        base_str = str(i) + "Fw" if i > 2 else "Fw" if i == 2 else "F"
        return_dict.update({base_str: p, base_str + "'": pi, base_str + "2": p2})
    for i, (p, pi, p2) in enumerate(zip(Rs, Rs_inv, Rs_double), start=1):
        base_str = str(i) + "Rw" if i > 2 else "Rw" if i == 2 else "R"
        return_dict.update({base_str: p, base_str + "'": pi, base_str + "2": p2})
    for i, (p, pi, p2) in enumerate(zip(Bs, Bs_inv, Bs_double), start=1):
        base_str = str(i) + "Bw" if i > 2 else "Bw" if i == 2 else "B"
        return_dict.update({base_str: p, base_str + "'": pi, base_str + "2": p2})
    for i, (p, pi, p2) in enumerate(zip(Ls, Ls_inv, Ls_double), start=1):
        base_str = str(i) + "Lw" if i > 2 else "Lw" if i == 2 else "L"
        return_dict.update({base_str: p, base_str + "'": pi, base_str + "2": p2})
    for i, (p, pi, p2) in enumerate(zip(Ds, Ds_inv, Ds_double), start=1):
        base_str = str(i) + "Dw" if i > 2 else "Dw" if i == 2 else "D"
        return_dict.update({base_str: p, base_str + "'": pi, base_str + "2": p2})

    return return_dict


def apply_moves_to_permutation(
    permutation: CubePermutation, sequence: MoveSequence, cube_size: int = CUBE_SIZE
) -> CubePermutation:
    """Apply a sequence of moves to the permutation.

    Args:
        permutation (CubePermutation): State of the cube.
        sequence (MoveSequence): Sequence of moves.
        cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.

    Returns:
        CubePermutation: Permutation after applying the moves.
    """
    permutations = create_permutations(cube_size=cube_size)

    for move in sequence:
        permutation = permutation[permutations[move]]

    return permutation
