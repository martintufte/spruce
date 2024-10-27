import numpy as np

from rubiks_cube.configuration import CUBE_SIZE
from rubiks_cube.configuration.enumeration import Piece
from rubiks_cube.configuration.type_definitions import CubeMask
from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.state.permutation import apply_moves_to_state
from rubiks_cube.state.permutation import get_identity_permutation


def get_ones_mask(cube_size: int = CUBE_SIZE) -> CubeMask:
    """Return the ones mask of the cube.

    Args:
        cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.

    Returns:
        CubeMask: Identity mask.
    """

    assert 1 <= cube_size <= 10, "Size must be between 1 and 10."

    return np.ones(6 * cube_size**2, dtype=bool)


def get_zeros_mask(cube_size: int = CUBE_SIZE) -> CubeMask:
    """Return the zeros mask of the cube.

    Args:
        cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.

    Returns:
        CubeMask: Identity mask.
    """

    assert 1 <= cube_size <= 10, "Size must be between 1 and 10."

    return np.zeros(6 * cube_size**2, dtype=bool)


def combine_masks(masks: tuple[CubeMask, ...]) -> CubeMask:
    """Find the total mask from multiple masks of progressively smaller sizes."""

    mask = masks[0].copy()
    if len(masks) > 1:
        mask[mask] = combine_masks(masks[1:])
    return mask


def get_rubiks_cube_mask(
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
    identity_permutation = get_identity_permutation(cube_size=cube_size)
    permutation = apply_moves_to_state(identity_permutation, sequence, cube_size)

    mask: CubeMask
    if invert:
        mask = permutation != identity_permutation
    else:
        mask = permutation == identity_permutation

    return mask


def get_piece_mask(piece: Piece | list[Piece | None], cube_size: int = CUBE_SIZE) -> CubeMask:
    """Return a mask for the piece type.

    Args:
        pieces (Piece | list[Piece]): Piece type(s).
        cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.

    Returns:
        CubeMask: Mask for the piece type.
    """

    if isinstance(piece, list):
        mask = get_zeros_mask(cube_size=cube_size)
        for p in piece:
            if p is not None:
                mask |= get_piece_mask(p, cube_size=cube_size)
        return mask

    face_mask = np.zeros((cube_size, cube_size), dtype=bool)
    if piece is Piece.corner:
        if cube_size == 1:
            face_mask[0, 0] = True
        elif cube_size > 1:
            face_mask[0, 0] = True
            face_mask[0, cube_size - 1] = True
            face_mask[cube_size - 1, 0] = True
            face_mask[cube_size - 1, cube_size - 1] = True
    elif piece is Piece.edge:
        if cube_size > 2:
            face_mask[0, 1 : cube_size - 1] = True
            face_mask[cube_size - 1, 1 : cube_size - 1] = True
            face_mask[1 : cube_size - 1, 0] = True
            face_mask[1 : cube_size - 1, cube_size - 1] = True
    elif piece is Piece.center:
        if cube_size > 2:
            face_mask[1 : cube_size - 1, 1 : cube_size - 1] = True

    return np.tile(face_mask.flatten(), 6)
