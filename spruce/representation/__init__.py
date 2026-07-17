from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from typing import Final

from spruce.representation.utils import get_identity
from spruce.representation.utils import invert

if TYPE_CHECKING:
    from spruce.move.meta import MoveMeta
    from spruce.move.sequence import MoveSequence
    from spruce.types import PermutationArray

LOGGER: Final = logging.getLogger(__name__)


def _substitute_moves(moves: list[str], move_meta: MoveMeta) -> list[str]:
    """Return the moves with substitutions applied, flattening multi-move expansions."""
    out: list[str] = []
    for move in moves:
        new_moves = move_meta.substitute(move)
        if isinstance(new_moves, str):
            out.append(new_moves)
        else:
            out.extend(new_moves)
    return out


def _truncate_at_rotation(moves: list[str], move_meta: MoveMeta) -> list[str]:
    """Return the moves up to (excluding) the first rotation move."""
    rotation_moves = move_meta.rotation_moves
    for index, move in enumerate(moves):
        if move in rotation_moves:
            return moves[:index]
    return moves


def _apply_moves(
    permutation: PermutationArray,
    moves: list[str],
    permutations: dict[str, PermutationArray],
) -> PermutationArray:
    """Compose the moves onto the permutation.

    Uses ndarray.take over fancy indexing as it is measurably faster for small arrays.
    """
    for move in moves:
        permutation = permutation.take(permutations[move])
    return permutation


def get_rubiks_cube_permutation(
    sequence: MoveSequence,
    move_meta: MoveMeta,
    initial_permutation: PermutationArray | None = None,
    use_inverse: bool = True,
    orientate_after: bool = False,
    invert_after: bool = False,
) -> PermutationArray:
    """Get the cube permutation from a sequence of moves.

    Args:
        sequence (MoveSequence): Rubiks cube move sequence.
        move_meta (MoveMeta): Meta information about moves.
        initial_permutation (PermutationArray, optional): Initial permutation of the cube.
        use_inverse (bool, optional): Use the inverse part. Defaults to True.
        orientate_after (bool, optional): Orientate to same orientation as the
            initial permutation. Defaults to False.
        invert_after (bool, optional): Whether to invert after applying moves. Defaults to False.

    Returns:
        PermutationArray: The Rubiks cube permutation.
    """
    permutations = move_meta.permutations
    normal = sequence.normal
    inverse = sequence.inverse if use_inverse else []

    # Substitute moves, shift rotations to the end, and drop them if orientate after
    if orientate_after:
        normal = move_meta.shift_rotations_to_end(
            _substitute_moves(normal, move_meta), canonicalize=False
        )
        inverse = move_meta.shift_rotations_to_end(
            _substitute_moves(inverse, move_meta), canonicalize=False
        )
        normal = _truncate_at_rotation(normal, move_meta)
        inverse = _truncate_at_rotation(inverse, move_meta)

    # Create permutation
    if initial_permutation is not None:
        assert initial_permutation.size == move_meta.size
        permutation = initial_permutation
    else:
        permutation = get_identity(size=move_meta.size)

    # Apply moves on inverse
    if inverse:
        permutation = invert(_apply_moves(invert(permutation), inverse, permutations))

    # Apply moves on normal
    permutation = _apply_moves(permutation, normal, permutations)

    if invert_after:
        return invert(permutation)
    if permutation is initial_permutation:
        return permutation.copy()
    return permutation
