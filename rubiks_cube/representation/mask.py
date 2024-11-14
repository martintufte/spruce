from collections.abc import Sequence

import numpy as np

from rubiks_cube.configuration import CUBE_SIZE
from rubiks_cube.configuration.enumeration import Piece
from rubiks_cube.configuration.types import CubeMask
from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.representation.permutation import apply_moves_to_permutation
from rubiks_cube.representation.permutation import get_identity_permutation


def get_ones_mask(cube_size: int = CUBE_SIZE) -> CubeMask:
    """
    Return the ones mask of the cube.

    Args:
        cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.

    Returns:
        CubeMask: Identity mask.
    """
    assert 1 <= cube_size <= 10, "Size must be between 1 and 10."

    return np.ones(6 * cube_size**2, dtype=bool)


def get_zeros_mask(cube_size: int = CUBE_SIZE) -> CubeMask:
    """
    Return the zeros mask of the cube.

    Args:
        cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.

    Returns:
        CubeMask: Identity mask.
    """
    assert 1 <= cube_size <= 10, "Size must be between 1 and 10."

    return np.zeros(6 * cube_size**2, dtype=bool)


def combine_masks(masks: Sequence[CubeMask]) -> CubeMask:
    """Find the total mask from multiple masks of progressively smaller sizes."""
    mask = masks[0].copy()
    if len(masks) > 1:
        mask[mask] = combine_masks(masks[1:])
    return mask


def get_rubiks_cube_mask(
    sequence: MoveSequence | None = None,
    invert: bool = False,
    cube_size: int = CUBE_SIZE,
) -> CubeMask:
    """Create a boolean mask of pieces that remain solved after sequence.

    Args:
        sequence (MoveSequence | None, optional): Move sequence. Defaults to None.
        invert (bool, optional): Whether to invert the state. Defaults to False.
        cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.

    Returns:
        CubeMask: Boolean mask of pieces that remain solved after sequence.
    """
    if sequence is None:
        sequence = MoveSequence()

    identity_permutation = get_identity_permutation(cube_size=cube_size)
    permutation = apply_moves_to_permutation(identity_permutation, sequence, cube_size)

    mask: CubeMask
    mask = permutation != identity_permutation if invert else permutation == identity_permutation

    return mask


def get_piece_mask(piece: Piece | list[Piece], cube_size: int = CUBE_SIZE) -> CubeMask:
    """
    Return a mask for the piece type.

    Args:
        piece (Piece | list[Piece]): Piece type(s).
        cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.

    Returns:
        CubeMask: Mask for the piece type.
    """
    if isinstance(piece, list):
        mask = get_zeros_mask(cube_size=cube_size)
        for p in piece:
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


def get_single_piece_mask(
    piece: Piece,
    first_idx: int = 1,
    second_idx: int = 1,
    cube_size: int = CUBE_SIZE,
) -> CubeMask:
    """
    Return a mask for a single piece.

    Args:
        piece (Piece): Piece type.
        first_idx (int, optional): First index. Defaults to 1.
        second_idx (int, optional): Second index. Defaults to 1.
        cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.

    Returns:
        CubeMask: Mask for the single piece.
    """
    if cube_size == 1:
        if piece is Piece.corner:
            return get_ones_mask(cube_size=cube_size)
        return get_zeros_mask(cube_size=cube_size)

    if piece is Piece.corner:
        return get_coord_mask((0, 0), cube_size=cube_size)

    elif piece is Piece.edge:
        return get_coord_mask((0, second_idx), cube_size=cube_size)

    elif piece is Piece.center:
        return get_coord_mask((first_idx, second_idx), cube_size=cube_size)


def get_coord_mask(coord: tuple[int, int], cube_size: int = CUBE_SIZE) -> CubeMask:
    """
    Return a mask for a single piece.

    Args:
        coord (tuple[int, int]): Coordinates of the piece.
        cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.

    Returns:
        CubeMask: Mask for the single piece.
    """
    assert 0 <= max(coord) < cube_size / 2, "Coordinates must be within the cube."

    # The whole cube is a single piece
    if cube_size == 1:
        return get_ones_mask(cube_size=cube_size)

    mask = get_zeros_mask(cube_size=cube_size)

    # Set the ULB corner
    if coord == (0, 0):
        mask[0] = True
        mask[3 * cube_size**2 + cube_size - 1] = True
        mask[4 * cube_size**2] = True

    # Set the UB edge
    elif coord[0] == 0:
        edge_idx = coord[1]
        if cube_size > 2:
            mask[edge_idx] = True
            mask[3 * cube_size**2 + cube_size - 1 - edge_idx] = True

    # Set the U center
    elif cube_size > 2:
        mask[coord[0] * cube_size + coord[1]] = True

    return mask
