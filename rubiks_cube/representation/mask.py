from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING
from typing import cast

import numpy as np

from rubiks_cube.configuration.enumeration import Piece
from rubiks_cube.move.meta import MoveMeta
from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.representation import get_rubiks_cube_permutation
from rubiks_cube.representation.permutation import create_permutations
from rubiks_cube.representation.utils import get_identity

if TYPE_CHECKING:
    from collections.abc import Sequence

    from rubiks_cube.configuration.types import CubeMask


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


def get_fixed_mask(sequence: MoveSequence, move_meta: MoveMeta) -> CubeMask:
    """Create a boolean mask of indices that remain fixed after applying the sequence.

    Args:
        sequence (MoveSequence): Move sequence.
        move_meta (MoveMeta): Meta information about moves.

    Returns:
        CubeMask: Boolean mask of pieces that remain fixed after sequence.
    """
    permutation = get_rubiks_cube_permutation(sequence, move_meta=move_meta)
    return cast("CubeMask", permutation == get_identity(permutation.size))


@lru_cache(maxsize=10)
def get_fixed_piece_mask_map(cube_size: int) -> dict[Piece, CubeMask]:
    move_meta = MoveMeta.from_cube_size(cube_size)

    edge_mask = get_fixed_mask(
        sequence=MoveSequence(["E2", "R", "L", "S2", "L", "R'", "S2", "R2", "S", "M", "S", "M'"]),
        move_meta=move_meta,
    )
    corner_mask = get_fixed_mask(sequence=MoveSequence(["M'", "S", "E"]), move_meta=move_meta)
    center_mask = get_fixed_mask(sequence=MoveSequence(["R", "L", "U", "D"]), move_meta=move_meta)
    return {
        Piece.center: center_mask,
        Piece.corner: corner_mask,
        Piece.edge: edge_mask,
    }


def get_pieces_mask(pieces: Sequence[Piece], move_meta: MoveMeta) -> CubeMask:
    """Return a mask for the piece type.

    Args:
        pieces (Sequence[Piece]): Pieces.
        move_meta (MoveMeta): Meta information about the moves.

    Returns:
        CubeMask: Mask for the piece type.
    """
    fixed_piece_mask_map = get_fixed_piece_mask_map(move_meta.cube_size)

    mask = get_zeros_mask(cube_size=move_meta.cube_size)
    for piece in pieces:
        piece_mask = fixed_piece_mask_map[piece]
        mask |= piece_mask
    return mask


def get_facelet_mask(
    piece: Piece,
    cube_size: int,
    first_idx: int = 1,
    second_idx: int = 1,
) -> CubeMask:
    """Return a mask for a single facelet.

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
    piece_mask = get_facelet_mask(piece, cube_size=cube_size)
    return generate_piece_symmetries(piece_mask=piece_mask, cube_size=cube_size)
