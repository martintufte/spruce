from __future__ import annotations

from enum import Enum
from enum import unique
from typing import TYPE_CHECKING
from typing import cast

import numpy as np

from spruce.algebra import get_permutation
from spruce.algebra.permutation import get_identity
from spruce.puzzle.cube.notation import parse_sequence

if TYPE_CHECKING:
    from collections.abc import Sequence

    from spruce.algebra.group import MoveMeta
    from spruce.move.sequence import MoveSequence
    from spruce.types import MaskArray


@unique
class Piece(Enum):
    center = "center"
    corner = "corner"
    edge = "edge"


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
    permutation = get_permutation(sequence, move_meta=move_meta)
    return cast("MaskArray", permutation == get_identity(permutation.size))


def get_fixed_piece_mask_map(move_meta: MoveMeta) -> dict[Piece, MaskArray]:
    edge_mask = get_fixed_mask(
        sequence=parse_sequence(move_meta=move_meta, string="E2 R L S2 L R' S2 R2 S M S M'"),
        move_meta=move_meta,
    )
    corner_mask = get_fixed_mask(
        sequence=parse_sequence(move_meta=move_meta, string="M' S E"), move_meta=move_meta
    )
    center_mask = get_fixed_mask(
        sequence=parse_sequence(move_meta=move_meta, string="R L U D"), move_meta=move_meta
    )
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
    fixed_piece_mask_map = get_fixed_piece_mask_map(move_meta=move_meta)

    mask = get_zeros_mask(size=move_meta.size)
    for piece in pieces:
        piece_mask = fixed_piece_mask_map[piece]
        mask |= piece_mask
    return mask
