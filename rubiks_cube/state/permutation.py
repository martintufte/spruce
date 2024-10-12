from __future__ import annotations

from functools import lru_cache
from functools import reduce
from typing import TYPE_CHECKING

import numpy as np

from rubiks_cube.configuration import CUBE_SIZE
from rubiks_cube.configuration.enumeration import Piece
from rubiks_cube.move.generator import MoveGenerator
from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.state.utils import invert
from rubiks_cube.state.utils import multiply
from rubiks_cube.state.utils import rotate_face

if TYPE_CHECKING:
    from rubiks_cube.configuration.type_definitions import CubeMask
    from rubiks_cube.configuration.type_definitions import CubePermutation
    from rubiks_cube.configuration.type_definitions import CubeState


def get_identity_permutation(cube_size: int = CUBE_SIZE) -> CubePermutation:
    """Return the identity permutation of the cube.

    Args:
        cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.

    Returns:
        CubeState: Identity permutation.
    """

    assert 1 <= cube_size <= 10, "Size must be between 1 and 10."

    return np.arange(6 * cube_size**2, dtype="int")


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


def create_mask_from_sequence(
    sequence: MoveSequence = MoveSequence(),
    invert: bool = False,
    cube_size: int = CUBE_SIZE,
) -> CubeMask:
    """Create a boolean mask of pieces that remain solved after sequence.

    Args:
        sequence (MoveSequence, optional): Move sequence. Defaults to MoveSequence().
        invert (bool, optional): Whether to invert the state. Defaults to False.
        cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.

    Returns:
        CubeMask: Boolean mask of pieces that remain solved after sequence.
    """
    solved_state = get_identity_permutation(cube_size=cube_size)
    permutation = apply_moves_to_state(solved_state, sequence, cube_size)

    mask: CubeMask
    if invert:
        mask = permutation != solved_state
    else:
        mask = permutation == solved_state

    return mask


def generate_mask_symmetries(
    masks: list[CubeMask],
    generator: MoveGenerator = MoveGenerator("<x, y>"),
    max_size: int = 60,
    cube_size: int = CUBE_SIZE,
) -> list[list[CubeMask]]:
    """Generate list of mask symmetries of the cube using the generator.

    Args:
        masks (list[CubeMask]): List of masks.
        generator (MoveGenerator, optional): Move generator. Defaults to MoveGenerator("<x, y>").
        max_size (int, optional): Max size of the symmetry group. Defaults to 60.
        cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.

    Raises:
        ValueError: Symmetries is too large.

    Returns:
        list[list[CubeMask]]: List of mask symmetries.
    """

    solved_state = get_identity_permutation(cube_size=cube_size)
    permutations = [
        apply_moves_to_state(solved_state, sequence, cube_size=cube_size) for sequence in generator
    ]

    group_of_masks: list[list[CubeMask]] = [masks]
    size = len(group_of_masks)

    while True:
        for masks in group_of_masks:
            for p in permutations:
                new_masks = [mask[p] for mask in masks]
                if not any(
                    all(
                        np.array_equal(new_mask, current_mask)
                        for new_mask, current_mask in zip(new_masks, current_masks)
                    )
                    for current_masks in group_of_masks
                ):
                    group_of_masks.append(new_masks)
        if len(group_of_masks) == size:
            break
        size = len(group_of_masks)
        if size > max_size:
            raise ValueError(f"Symmetries is too large, {len(group_of_masks)} > {max_size}!")

    return group_of_masks


def generate_permutation_symmetries(
    mask: CubeMask,
    generator: MoveGenerator = MoveGenerator("<x, y>"),
    max_size: int = 60,
    cube_size: int = CUBE_SIZE,
) -> list[CubeState]:
    """Generate list of permutations of the cube using the generator.

    Args:
        mask (CubeMask): Mask of the cube.
        generator (MoveGenerator, optional): Move generator. Defaults to MoveGenerator("<x, y>").
        max_size (int, optional): Max size of the symmetries. Defaults to 60.
        cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.

    Raises:
        ValueError: Symmetries is too large.

    Returns:
        list[CubeState]: List of permutations.
    """

    solved_state = get_identity_permutation(cube_size=cube_size)
    permutations = [
        apply_moves_to_state(solved_state, sequence, cube_size=cube_size) for sequence in generator
    ]

    list_of_permutations: list[CubeState] = [solved_state]
    size = len(list_of_permutations)

    while True:
        for current_permutation in list_of_permutations:
            for permutation in permutations:
                new_permutation = current_permutation[permutation]
                if not any(
                    np.array_equal(mask[new_permutation], mask[perm])
                    for perm in list_of_permutations
                ):
                    list_of_permutations.append(new_permutation)
        if len(list_of_permutations) == size:
            break
        size = len(list_of_permutations)
        if size > max_size:
            raise ValueError(f"Symmetries is too large, {len(list_of_permutations)} > {max_size}!")

    return list_of_permutations


def generate_indices_symmetries(
    mask: CubeMask,
    generator: MoveGenerator = MoveGenerator("<x, y>"),
    cube_size: int = CUBE_SIZE,
) -> list[CubeState]:
    """Generate list of indices symmetries of the cube using the generator.

    Args:
        mask (CubeMask): Mask of the cube.
        generator (MoveGenerator, optional): Move generator. Defaults to MoveGenerator("<x, y>").
        cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.

    Returns:
        list[CubeState]: List of indices symmetries.
    """

    solved_state = get_identity_permutation(cube_size=cube_size)
    permutations = [
        apply_moves_to_state(solved_state, sequence, cube_size=cube_size) for sequence in generator
    ]

    list_of_states: list[CubeState] = [solved_state[mask]]
    size = len(list_of_states)

    while True:
        for perm in permutations:
            new_states = [perm[state] for state in list_of_states]
            for new_state in new_states:
                if not any(
                    np.array_equal(new_state, current_state) for current_state in list_of_states
                ):
                    list_of_states.append(new_state)
        if len(list_of_states) == size:
            break
        size = len(list_of_states)

    return list_of_states


def indices2ordered_mask(indices: CubeState, cube_size: int = CUBE_SIZE) -> CubeState:
    """Convert indices to an ordered mask.

    Args:
        indices (CubeState): Indices of the cube.
        cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.

    Returns:
        CubeState: Ordered mask.
    """
    solved_state = get_identity_permutation(cube_size=cube_size)
    ordered_mask = np.zeros_like(solved_state, dtype=int)
    ordered_mask[indices] = np.arange(1, len(indices) + 1)  # 1-indexed
    return ordered_mask


def indices2mask(indices: CubeState, cube_size: int = CUBE_SIZE) -> CubeMask:
    """Convert indices to a mask.

    Args:
        indices (CubeState): Indices of the cube.
        cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.

    Returns:
        CubeMask: Mask.
    """
    solved_state = get_identity_permutation(cube_size=cube_size)
    mask = np.zeros_like(solved_state, dtype=bool)
    mask[indices] = True
    return mask


def ordered_mask2indices(mask: CubeState, cube_size: int = CUBE_SIZE) -> CubeState:
    """Convert an ordered mask to indices.

    Args:
        mask (CubeState): Ordered mask.
        cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.

    Returns:
        CubeState: Indices.
    """
    indices = np.where(mask)[0]
    return indices[np.argsort(mask[indices])]


def get_example_piece_mask(piece: Piece, cube_size: int = CUBE_SIZE) -> CubeMask:
    """Return an example piece of the cube, a mask with only one index.

    Args:
        piece (Piece): Piece type.
        cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.

    Returns:
        CubeState: First example piece.
    """
    mask = np.zeros(6 * cube_size**2, dtype=bool)

    # up-front-right corner
    if piece is Piece.corner:
        mask[cube_size**2 - 1] = True
        mask[cube_size**2 + cube_size - 1] = True
        mask[2 * cube_size**2] = True

    # up-front edge (closest to the corner)
    elif piece is Piece.edge:
        mask[cube_size**2 - 2] = True
        mask[cube_size**2 + cube_size - 2] = True

    # up center
    elif piece is Piece.center:
        mask[int((cube_size**2 - 1) // 2)] = True

    return mask


@lru_cache(maxsize=1)
def get_all_piece_idx_sets(cube_size: int = CUBE_SIZE) -> list[list[int]]:
    """Return all indexes of the pieces on the cube.

    Args:
        cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.

    Returns:
        list[list[int]]: List of indexes of the pieces on the cube.
    """
    pieces = [Piece.corner, Piece.edge]
    idx_list = []
    for piece in pieces:
        mask = get_example_piece_mask(piece, cube_size=cube_size)
        idx_list.extend(
            [
                list(np.where(symmetry[0])[0])
                for symmetry in generate_mask_symmetries([mask], cube_size=cube_size)
            ]
        )
    return idx_list


# TODO: This function only works for corner, edge and center pieces. Expand to
# all pieces on bigger cubes.
@lru_cache(maxsize=3)
def get_piece_mask(piece: Piece, cube_size: int = CUBE_SIZE) -> CubeMask:
    """Return a mask for the piece type.

    Args:
        piece (Piece): Piece type.
        cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.

    Returns:
        CubeMask: Mask for the piece type.
    """
    n2 = cube_size**2

    if piece is Piece.corner:
        mask = np.zeros(6 * n2, dtype=bool)
        for i in range(6):
            mask[n2 * i] = True
            mask[n2 * i + cube_size - 1] = True
            mask[n2 * i + n2 - cube_size] = True
            mask[n2 * i + n2 - 1] = True

    elif piece is Piece.edge:
        mask = np.zeros(6 * n2, dtype=bool)
        if cube_size % 2 == 1:
            for i in range(6):
                half = int(cube_size // 2)
                face_idx = int(n2 // 2)
                mask[n2 * i + half] = True
                mask[n2 * i + face_idx - half] = True
                mask[n2 * i + face_idx + half] = True
                mask[n2 * i + n2 - 1 - half] = True

    elif piece is Piece.center:
        mask = np.zeros(6 * n2, dtype=bool)
        if cube_size % 2 == 1:
            face_idx = int(n2 // 2)
            for i in range(6):
                mask[n2 * i + face_idx] = True

    return mask


def unorientate_mask(mask: CubeMask, cube_size: int = CUBE_SIZE) -> CubeMask:
    """Turn the orientated mask into an unorientated mask.

    Args:
        mask (CubeMask): Mask of the cube.
        cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.

    Returns:
        CubeMask: Unorientated mask.
    """
    new_mask = mask.copy()
    for idx in np.where(mask)[0]:
        for piece_idx_list in get_all_piece_idx_sets(cube_size=cube_size):
            if idx in piece_idx_list:
                new_mask[piece_idx_list] = True
    return new_mask


def get_generator_orientation(
    piece: Piece,
    generator: MoveGenerator,
    cube_size: int = CUBE_SIZE,
) -> list[CubeMask]:
    """Return a list of masks for the piece orientation.

    Args:
        piece (Piece): Piece type.
        generator (MoveGenerator): Move generator.
        cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.

    Returns:
        list[CubeMask]: List of masks for the piece orientation.
    """

    # All indexes of the piece on the cube
    piece_mask = get_piece_mask(piece, cube_size)

    # All indexes of the piece affected by the generator
    affected_mask = reduce(
        np.logical_or,
        (
            create_mask_from_sequence(sequence=sequence, invert=True, cube_size=cube_size)
            for sequence in generator
        ),
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
        solved_state = get_identity_permutation(cube_size=cube_size)
        mask = np.zeros_like(solved_state, dtype=bool)
        mask[oriented_piece] = True

        # All symmetries for the piece
        symmetries = generate_mask_symmetries(
            masks=[mask],
            generator=generator,
            cube_size=cube_size,
        )
        # unpack the first element in the lists
        symmetry_group = [symmetry[0] for symmetry in symmetries]

        # All symmetries for the piece
        orientated_mask = reduce(np.logical_or, symmetry_group)
        unorientated_mask = unorientate_mask(orientated_mask, cube_size=cube_size)

        orientations.append(orientated_mask)

        # Remove the un-oriented mask
        affected_piece_mask[unorientated_mask] = False

    return orientations


def orientations_are_equal(orients1: list[CubeState], orients2: list[CubeState]) -> bool:
    """Check if two orientations are equal.

    Args:
        orients1 (list[CubeState]): First list of orientations.
        orients2 (list[CubeState]): Second list of orientations.

    Returns:
        bool: Whether the orientations are equal.
    """

    while orients1:
        orient1 = orients1.pop()
        for i, orient2 in enumerate(orients2):
            if np.array_equal(orient1, orient2):
                del orients2[i]
                break
        else:
            return False
    return not orients2


def apply_moves_to_state(
    state: CubeState, sequence: MoveSequence, cube_size: int = CUBE_SIZE
) -> CubeState:
    """Apply a sequence of moves to the permutation.

    Args:
        state (CubeState): State of the cube.
        sequence (MoveSequence): Sequence of moves.
        cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.

    Returns:
        CubeState: Permutation after applying the moves.
    """
    permutations = create_permutations(cube_size=cube_size)

    for move in sequence:
        state = state[permutations[move]]

    return state
