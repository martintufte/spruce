from __future__ import annotations

from functools import lru_cache
from functools import reduce

import numpy as np

from rubiks_cube.configuration import CUBE_SIZE
from rubiks_cube.permutation.utils import rotate_face
from rubiks_cube.permutation.utils import multiply
from rubiks_cube.permutation.utils import inverse
from rubiks_cube.utils.enumerations import Piece
from rubiks_cube.utils.sequence import cleanup
from rubiks_cube.utils.sequence import MoveSequence
from rubiks_cube.utils.move import is_rotation

SOLVED_STATE = np.arange(6 * CUBE_SIZE**2, dtype="int")


@lru_cache(maxsize=1)
def create_permutations(size: int = CUBE_SIZE) -> dict[str, np.ndarray]:
    """Return a dictionaty over all legal turns."""

    assert 1 <= size <= 10, "Size must be minimum size 1 and maximum size 10."

    # Define the identity permutation
    face_size = size**2
    IDENTITY = SOLVED_STATE.copy()

    # Define faces
    UP = slice(0, face_size)
    FRONT = slice(face_size, 2 * face_size)
    RIGHT = slice(2 * face_size, 3 * face_size)
    BACK = slice(3 * face_size, 4 * face_size)
    LEFT = slice(4 * face_size, 5 * face_size)
    DOWN = slice(5 * face_size, 6 * face_size)

    # Define rotation x
    x = np.copy(IDENTITY)
    x[UP] = IDENTITY[FRONT]
    x[FRONT] = IDENTITY[DOWN]
    x[RIGHT] = rotate_face(IDENTITY, RIGHT, -1)
    x[BACK] = rotate_face(IDENTITY, UP, 2)
    x[LEFT] = rotate_face(IDENTITY, LEFT, 1)
    x[DOWN] = rotate_face(IDENTITY, BACK, 2)

    # Define rotation y
    y = np.copy(IDENTITY)
    y[UP] = rotate_face(IDENTITY, UP, -1)
    y[FRONT] = IDENTITY[RIGHT]
    y[RIGHT] = IDENTITY[BACK]
    y[BACK] = IDENTITY[LEFT]
    y[LEFT] = IDENTITY[FRONT]
    y[DOWN] = rotate_face(IDENTITY, DOWN, 1)

    # Define up face rotations (U, Uw, 3Uw, ... (n-1)Uw)
    U_list = []
    for i in range(1, size):
        U = np.copy(IDENTITY)
        affected = slice(0, i * size)
        U[UP] = rotate_face(IDENTITY, UP, -1)
        U[FRONT][affected] = IDENTITY[RIGHT][affected]
        U[RIGHT][affected] = IDENTITY[BACK][affected]
        U[BACK][affected] = IDENTITY[LEFT][affected]
        U[LEFT][affected] = IDENTITY[FRONT][affected]
        U_list.append(U)

    return get_permutation_dictionary(size, IDENTITY, x, y, U_list)


def get_permutation_dictionary(
    size: int,
    IDENTITY: np.ndarray,
    x: np.ndarray,
    y: np.ndarray,
    Us: list[np.ndarray],
) -> dict[str, np.ndarray]:
    """Define all other permutations from I, x, y, U"""

    # Rotations with doubles and inverses
    # x (given)
    x2 = multiply(x, 2)
    xi = inverse(x)
    # y (given)
    y2 = multiply(y, 2)
    yi = inverse(y)
    z = IDENTITY[x][y][xi]
    z2 = multiply(z, 2)
    zi = inverse(z)

    # Face turns with inverses and doubles
    # Us (given)
    Fs = [IDENTITY[x][U][xi] for U in Us]
    Rs = [IDENTITY[zi][U][z] for U in Us]
    Bs = [IDENTITY[xi][U][x] for U in Us]
    Ls = [IDENTITY[z][U][zi] for U in Us]
    Ds = [IDENTITY[x2][U][x2] for U in Us]

    Us_inv = [inverse(p) for p in Us]
    Fs_inv = [inverse(p) for p in Fs]
    Rs_inv = [inverse(p) for p in Rs]
    Bs_inv = [inverse(p) for p in Bs]
    Ls_inv = [inverse(p) for p in Ls]
    Ds_inv = [inverse(p) for p in Ds]

    Us_double = [multiply(p, 2) for p in Us]
    Fs_double = [multiply(p, 2) for p in Fs]
    Rs_double = [multiply(p, 2) for p in Rs]
    Bs_double = [multiply(p, 2) for p in Bs]
    Ls_double = [multiply(p, 2) for p in Ls]
    Ds_double = [multiply(p, 2) for p in Ds]

    # Identity
    return_dict = {"I": IDENTITY}

    # Rotations
    return_dict.update(
        {
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
    )

    # Slice turns for 3x3 and higher
    if size > 2:
        M = IDENTITY[Rs[0]][Rs_inv[-1]]
        M2 = multiply(M, 2)
        Mi = inverse(M)
        S = IDENTITY[Fs[-1]][Fs_inv[0]]
        S2 = multiply(S, 2)
        Si = inverse(S)
        E = IDENTITY[Us[0]][Us_inv[-1]]
        E2 = multiply(E, 2)
        Ei = inverse(E)
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
    if size == 4:
        r = IDENTITY[Rs[1]][Rs_inv[0]]
        r2 = multiply(r, 2)
        ri = inverse(r)
        el = IDENTITY[Ls[1]][Ls_inv[0]]
        l2 = multiply(el, 2)
        li = inverse(el)
        return_dict.update(
            {"r": r, "r2": r2, "r'": ri, "l": el, "l2": l2, "l'": li}
        )

    # Face turns
    for i, (p, pi, p2) in enumerate(zip(Us, Us_inv, Us_double), start=1):
        base_str = str(i) + "Uw" if i > 2 else "Uw" if i == 2 else "U"
        return_dict.update(
            {base_str: p, base_str + "'": pi, base_str + "2": p2}
        )
    for i, (p, pi, p2) in enumerate(zip(Fs, Fs_inv, Fs_double), start=1):
        base_str = str(i) + "Fw" if i > 2 else "Fw" if i == 2 else "F"
        return_dict.update(
            {base_str: p, base_str + "'": pi, base_str + "2": p2}
        )
    for i, (p, pi, p2) in enumerate(zip(Rs, Rs_inv, Rs_double), start=1):
        base_str = str(i) + "Rw" if i > 2 else "Rw" if i == 2 else "R"
        return_dict.update(
            {base_str: p, base_str + "'": pi, base_str + "2": p2}
        )
    for i, (p, pi, p2) in enumerate(zip(Bs, Bs_inv, Bs_double), start=1):
        base_str = str(i) + "Bw" if i > 2 else "Bw" if i == 2 else "B"
        return_dict.update(
            {base_str: p, base_str + "'": pi, base_str + "2": p2}
        )
    for i, (p, pi, p2) in enumerate(zip(Ls, Ls_inv, Ls_double), start=1):
        base_str = str(i) + "Lw" if i > 2 else "Lw" if i == 2 else "L"
        return_dict.update(
            {base_str: p, base_str + "'": pi, base_str + "2": p2}
        )
    for i, (p, pi, p2) in enumerate(zip(Ds, Ds_inv, Ds_double), start=1):
        base_str = str(i) + "Dw" if i > 2 else "Dw" if i == 2 else "D"
        return_dict.update(
            {base_str: p, base_str + "'": pi, base_str + "2": p2}
        )

    return return_dict


def create_mask(
    sequence: MoveSequence | str = MoveSequence(),
    invert: bool = False,
    orientate_after: bool = False,
) -> np.ndarray:
    """Create a permutation mask of pieces that remain solved."""
    if isinstance(sequence, str):
        sequence = MoveSequence(sequence)
    permutation = get_permutation(sequence, orientate_after=orientate_after)

    if invert:
        return permutation != SOLVED_STATE
    return permutation == SOLVED_STATE


def generate_mask_symmetries(
    masks: list[np.ndarray],
    generator: list[np.ndarray] | None = None,
    max_size: int = 120,
) -> list[list[np.ndarray]]:
    """Generate all symmetries of the cube using the permutation."""

    # Set symmetries to default if None
    if generator is None:
        PERMUTATIONS = create_permutations(CUBE_SIZE)
        generator = [PERMUTATIONS["x"], PERMUTATIONS["y"]]

    group_of_masks: list[list[np.ndarray]] = [masks]
    size = len(group_of_masks)

    while True:
        for masks in group_of_masks:
            for g in generator:
                new_masks = [mask[g] for mask in masks]
                if not any(
                    all(
                        np.array_equal(new_mask, current_mask)
                        for new_mask, current_mask in zip(
                            new_masks, current_masks
                        )
                    )
                    for current_masks in group_of_masks
                ):
                    group_of_masks.append(new_masks)
        if len(group_of_masks) == size:
            break
        size = len(group_of_masks)
        if size > max_size:
            raise ValueError(
                f"Symmetries is too large, {len(group_of_masks)} > {max_size}!"
            )

    return group_of_masks


def get_example_piece(piece: Piece) -> np.ndarray:
    """Return an example piece of the cube."""
    mask = np.zeros(6 * CUBE_SIZE**2, dtype=bool)

    # Up-Front-Right corner
    if piece is Piece.corner:
        mask[CUBE_SIZE**2 - 1] = True
        mask[CUBE_SIZE**2 + CUBE_SIZE - 1] = True
        mask[2 * CUBE_SIZE**2] = True

    # Up-Front edge (closest to the corner)
    elif piece is Piece.edge:
        mask[CUBE_SIZE**2 - 2] = True
        mask[CUBE_SIZE**2 + CUBE_SIZE - 2] = True

    # Up center
    elif piece is Piece.center:
        mask[int((CUBE_SIZE**2 - 1) // 2)] = True

    return mask


@lru_cache(maxsize=1)
def get_all_piece_idx_sets() -> list[list[int]]:
    """Return all indexes of the pieces on the cube."""
    pieces = [Piece.corner, Piece.edge]
    idx_list = []
    for piece in pieces:
        mask = get_example_piece(piece)
        idx_list.extend(
            [
                list(np.where(symmetry[0])[0])
                for symmetry in generate_mask_symmetries([mask])
            ]
        )
    return idx_list


@lru_cache(maxsize=3)
def get_piece_mask(piece: Piece) -> np.ndarray:
    """Return a mask for the piece type."""
    n2 = CUBE_SIZE**2

    if piece is Piece.corner:
        mask = np.zeros(6 * n2, dtype=bool)
        for i in range(6):
            mask[n2 * i] = True
            mask[n2 * i + CUBE_SIZE - 1] = True
            mask[n2 * i + n2 - CUBE_SIZE] = True
            mask[n2 * i + n2 - 1] = True

    elif piece is Piece.edge:
        mask = np.zeros(6 * n2, dtype=bool)
        if CUBE_SIZE % 2 == 1:
            for i in range(6):
                half = int(CUBE_SIZE // 2)
                face_idx = int(n2 // 2)
                mask[n2 * i + half] = True
                mask[n2 * i + face_idx - half] = True
                mask[n2 * i + face_idx + half] = True
                mask[n2 * i + n2 - 1 - half] = True

    elif piece is Piece.center:
        mask = np.zeros(6 * n2, dtype=bool)
        if CUBE_SIZE % 2 == 1:
            face_idx = int(n2 // 2)
            for i in range(6):
                mask[n2 * i + face_idx] = True
    else:
        raise ValueError("Invalid piece type!")

    return mask


def unorientate_mask(mask: np.ndarray) -> np.ndarray:
    """Turn the orientated mask into an unorientated mask."""
    new_mask = mask.copy()
    for idx in np.where(mask)[0]:
        for piece_idx_list in get_all_piece_idx_sets():
            if idx in piece_idx_list:
                new_mask[piece_idx_list] = True
    return new_mask


def get_generator_orientation(
    piece: Piece,
    generator: str,
    orientate_after: bool = False,
) -> list[np.ndarray]:
    """Return a list of masks for the piece orientation."""

    # Split generator into moves
    assert generator[0] == "<", "Generator must start with '<'"
    assert generator[-1] == ">", "Generator must end with '>'"
    moves = generator[1:-1].split(",")

    # All indexes of the piece on the cube
    piece_mask = get_piece_mask(piece)

    # All indexes of the piece affected by the generator
    affected_mask = reduce(
        np.logical_or,
        (
            create_mask(
                sequence=move,
                invert=True,
                orientate_after=orientate_after,
            )
            for move in moves
        )
    )

    # All indexes of the piece affected by the generator
    affected_piece_mask = piece_mask & affected_mask

    # Keep track of all orientations
    orientations = []

    # Loop over all orientations of the piece
    while np.any(affected_piece_mask):

        # Index of the first oriented piece
        oriented_piece = np.argmax(affected_piece_mask)

        # Mask for the oriented piece
        mask = np.zeros_like(SOLVED_STATE, dtype=bool)
        mask[oriented_piece] = True

        # All symmetries for the piece
        symmetries = generate_mask_symmetries(
            masks=[mask],
            generator=[
                get_permutation(
                    sequence=MoveSequence(move),
                    orientate_after=True,
                )
                for move in moves
            ]
        )
        # unpack the first element in the lists
        symmetry_group = [symmetry[0] for symmetry in symmetries]

        # All symmetries for the piece
        orientated_mask = reduce(np.logical_or, symmetry_group)
        unorientated_mask = unorientate_mask(orientated_mask)

        orientations.append(orientated_mask)

        # Remove the un-oriented mask
        affected_piece_mask[unorientated_mask] = False

    return orientations


def get_permutation(
    sequence: MoveSequence,
    inverse_sequence: MoveSequence | None = None,
    starting_permutation: np.ndarray = SOLVED_STATE,
    orientate_after: bool = False,
) -> np.ndarray:
    """Get a cube permutation from a sequence of moves."""

    permutation_dict = create_permutations(CUBE_SIZE)
    permutation = starting_permutation.copy()

    if inverse_sequence is not None:
        inverse_permutation = get_permutation(
            inverse_sequence,
            starting_permutation=inverse(permutation),
            orientate_after=orientate_after,
        )
        permutation = inverse(inverse_permutation)

    for move in cleanup(sequence):
        if orientate_after and is_rotation(move):
            break
        permutation = permutation[permutation_dict[move]]

    return permutation


def orientation_is_equal(orient1: np.ndarray, orient2: np.ndarray) -> bool:
    """Check if two orientations are equal."""
    return np.array_equal(orient1, orient2)


def orientations_are_equal(
    orients1: list[np.ndarray], orients2: list[np.ndarray]
) -> bool:
    """Check if two orientations are equal."""

    while orients1:
        orient1 = orients1.pop()
        for i, orient2 in enumerate(orients2):
            if orientation_is_equal(orient1, orient2):
                del orients2[i]
                break
        else:
            return False
    return not orients2


def apply_move(permutation, move) -> np.ndarray:
    """Apply a move to the permutation."""
    PERMUTATIONS = create_permutations(CUBE_SIZE)

    return permutation[PERMUTATIONS[move]]


def apply_moves(permutation, sequence: MoveSequence) -> np.ndarray:
    """Apply a sequence of moves to the permutation."""
    for move in sequence:
        permutation = apply_move(permutation, move)

    return permutation


def main() -> None:
    # Test the create_permutations function
    sequence = MoveSequence("U R")
    PERMUTATIONS = create_permutations(CUBE_SIZE)
    mask = create_mask(sequence)
    generator = [PERMUTATIONS["x"], PERMUTATIONS["y"]]

    group = generate_mask_symmetries(masks=[mask, mask], generator=generator)
    print(f'"{sequence}" has group of length {len(group)}')


if __name__ == "__main__":
    main()
