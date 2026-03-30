from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING
from typing import cast

import numpy as np

from rubiks_cube.configuration.enumeration import Piece
from rubiks_cube.move.meta import MoveMeta
from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.representation import get_rubiks_cube_permutation
from rubiks_cube.representation.utils import get_identity

if TYPE_CHECKING:
    from collections.abc import Sequence

    from rubiks_cube.configuration.types import MaskArray


def get_zeros_mask(size: int) -> MaskArray:
    """Return the zeros mask for the given size."""
    return np.zeros(size, dtype=bool)


def get_ones_mask(size: int) -> MaskArray:
    """Return the ones mask for the given size."""
    return np.ones(size, dtype=bool)


def combine_masks(masks: Sequence[MaskArray]) -> MaskArray:
    """Find the total mask from multiple masks of progressively smaller sizes.

    Args:
        masks (Sequence[MaskArray]): Masks to combine.

    Returns:
        MaskArray: Combined mask.
    """
    mask = masks[0].copy()
    if len(masks) > 1:
        mask[mask] = combine_masks(masks[1:])
    return mask


def get_fixed_mask(sequence: MoveSequence, move_meta: MoveMeta) -> MaskArray:
    """Create a boolean mask of indices that remain fixed after applying the sequence.

    Args:
        sequence (MoveSequence): Move sequence.
        move_meta (MoveMeta): Meta information about moves.

    Returns:
        MaskArray: Boolean mask of pieces that remain fixed after sequence.
    """
    permutation = get_rubiks_cube_permutation(sequence, move_meta=move_meta)
    return cast("MaskArray", permutation == get_identity(permutation.size))


@lru_cache(maxsize=10)
def get_fixed_piece_mask_map(cube_size: int) -> dict[Piece, MaskArray]:
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


def get_pieces_mask(pieces: Sequence[Piece], move_meta: MoveMeta) -> MaskArray:
    """Return a mask for the piece type.

    Args:
        pieces (Sequence[Piece]): Pieces.
        move_meta (MoveMeta): Meta information about the moves.

    Returns:
        MaskArray: Mask for the piece type.
    """
    fixed_piece_mask_map = get_fixed_piece_mask_map(move_meta.cube_size)

    mask = get_zeros_mask(size=move_meta.size)
    for piece in pieces:
        piece_mask = fixed_piece_mask_map[piece]
        mask |= piece_mask
    return mask
