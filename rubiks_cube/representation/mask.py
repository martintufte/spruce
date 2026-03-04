from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING

import numpy as np

from rubiks_cube.configuration.enumeration import Piece
from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.representation import get_rubiks_cube_permutation
from rubiks_cube.representation.permutation import create_permutations
from rubiks_cube.representation.utils import get_identity

if TYPE_CHECKING:
    from collections.abc import Sequence

    from rubiks_cube.configuration.types import CubeMask
    from rubiks_cube.move.meta import MoveMeta


def get_zeros_mask(cube_size: int) -> CubeMask:
    """Return the zeros mask of the cube."""
    return np.zeros(6 * cube_size**2, dtype=bool)


def get_ones_mask(cube_size: int) -> CubeMask:
    """Return the ones mask of the cube."""
    return np.ones(6 * cube_size**2, dtype=bool)


def combine_masks(masks: Sequence[CubeMask]) -> CubeMask:
    """Find the total mask from multiple masks of progressively smaller sizes.

    Args:
        masks (Sequence[CubeMask]): Masks to combine.

    Returns:
        CubeMask: Combined mask.
    """
    mask = masks[0].copy()
    if len(masks) > 1:
        mask[mask] = combine_masks(masks[1:])
    return mask


def get_rubiks_cube_mask(sequence: MoveSequence, move_meta: MoveMeta) -> CubeMask:
    """Create a boolean mask of pieces that remain solved after applying the sequence.

    Args:
        sequence (MoveSequence): Move sequence.
        move_meta (MoveMeta): Meta information about moves.

    Returns:
        CubeMask: Boolean mask of pieces that remain solved after sequence.
    """
    if sequence is None:
        sequence = MoveSequence()

    permutation = get_rubiks_cube_permutation(sequence, move_meta=move_meta)

    mask: CubeMask
    mask = permutation == get_identity(permutation.size)

    return mask


def get_piece_mask(piece: Piece | list[Piece], cube_size: int) -> CubeMask:
    """Return a mask for the piece type.

    Args:
        piece (Piece | list[Piece]): Piece type(s).
        cube_size (int): Size of the cube.

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
    cube_size: int,
    first_idx: int = 1,
    second_idx: int = 1,
) -> CubeMask:
    """Return a mask for a single piece.

    Args:
        piece (Piece): Piece type.
        cube_size (int): Size of the cube.
        first_idx (int, optional): First index. Defaults to 1.
        second_idx (int, optional): Second index. Defaults to 1.

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


def get_coord_mask(coord: tuple[int, int], cube_size: int) -> CubeMask:
    """Return a mask for a single piece.

    Args:
        coord (tuple[int, int]): Coordinates of the piece.
        cube_size (int): Size of the cube.

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


def generate_piece_symmetries(piece_mask: CubeMask, cube_size: int) -> list[CubeMask]:
    """Generate list of piece symmetries of the cube.

    Args:
        piece_mask (CubeMask): Piece mask.
        cube_size (int): Cube size.

    Returns:
        list[CubePattern]: List of unique piece masks.

    Raises:
        ValueError: Piece symmetries is too large.
    """
    # Only need actions to generate all rotation states
    # TODO: Add mirror-permutation (i.e. flip 3D chirality)
    all_permutations = create_permutations(cube_size)
    actions = [all_permutations["x"], all_permutations["y"]]

    masks: list[CubeMask] = [piece_mask]
    size = len(masks)

    while True:
        for mask in masks:
            for action in actions:
                new_mask: CubeMask = mask[action]
                if not any(np.array_equal(new_mask, current_mask) for current_mask in masks):
                    masks.append(new_mask)
        if len(masks) == size:
            break
        size = len(masks)
        if size > 48:
            raise ValueError(f"Piece symmetries is too large, {len(masks)} > 48!")

    return masks


@lru_cache(maxsize=None)
def piece_masks(piece: Piece, cube_size: int) -> list[CubeMask]:
    """Generate the symmetries of a piece.

    Args:
        piece (Piece): Piece type.
        cube_size (int): Size of the cube.

    Returns:
        list[CubeMask]: List of piece symmetries.
    """
    piece_mask = get_single_piece_mask(piece, cube_size=cube_size)
    return generate_piece_symmetries(piece_mask=piece_mask, cube_size=cube_size)
