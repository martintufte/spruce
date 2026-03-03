from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from typing import Final

from rubiks_cube.configuration import CUBE_SIZE
from rubiks_cube.move.meta import MoveMeta
from rubiks_cube.move.sequence import decompose
from rubiks_cube.move.sequence import replace_slice_moves
from rubiks_cube.move.sequence import replace_wide_moves
from rubiks_cube.move.sequence import shift_rotations_to_end
from rubiks_cube.move.utils import is_rotation
from rubiks_cube.representation.permutation import get_identity_permutation
from rubiks_cube.representation.utils import invert

if TYPE_CHECKING:
    from rubiks_cube.configuration.types import CubePermutation
    from rubiks_cube.move.sequence import MoveSequence

LOGGER: Final = logging.getLogger(__name__)


def get_rubiks_cube_permutation(
    sequence: MoveSequence,
    move_meta: MoveMeta | None = None,
    initial_permutation: CubePermutation | None = None,
    use_inverse: bool = True,
    orientate_after: bool = False,
    invert_after: bool = False,
    cube_size: int = CUBE_SIZE,
) -> CubePermutation:
    """Get the cube permutation from a sequence of moves.

    Args:
        sequence (MoveSequence): Rubiks cube move sequence.
        move_meta (MoveMeta | None, optional): Meta information about moves. Defaults to None.
        initial_permutation (CubePermutation, optional): Initial permutation of the cube.
        use_inverse (bool, optional): Use the inverse part. Defaults to True.
        orientate_after (bool, optional): Orientate to same orientation as the
            initial permutation. Defaults to False.
        invert_after (bool, optional): Whether to invert after applying moves. Defaults to False.
        cube_size (int, optional): Size of the cube. Defaults to None.

    Returns:
        CubePermutation: The Rubiks cube permutation.
    """
    if move_meta is None:
        move_meta = MoveMeta.from_cube_size(cube_size)

    permutations = move_meta.permutations

    # Create permutation
    if initial_permutation is not None:
        assert initial_permutation.size == 6 * move_meta.cube_size**2
        permutation = initial_permutation.copy()
    else:
        permutation = get_identity_permutation(cube_size=move_meta.cube_size)

    # Decompose the sequence into normal and inverse moves, with rotations at the end
    normal_sequence, inverse_sequence = decompose(sequence)

    # Apply moves on inverse
    if use_inverse and inverse_sequence:
        # Safeguard for wide moves and slices
        replace_wide_moves(inverse_sequence, cube_size=move_meta.cube_size)
        replace_slice_moves(inverse_sequence)

        # Shift rotations to the end is orientate after
        if orientate_after:
            shift_rotations_to_end(inverse_sequence, move_meta)

        inverted_permutation = invert(permutation)
        for move in inverse_sequence:
            if orientate_after and is_rotation(move):
                break
            inverted_permutation = inverted_permutation[permutations[move]]
        permutation = invert(inverted_permutation)

    # Apply moves on normal
    if normal_sequence:
        # Safeguard for wide moves and slices
        replace_wide_moves(normal_sequence, cube_size=move_meta.cube_size)
        replace_slice_moves(normal_sequence)

        # Shift rotations to the end if orientate after
        if orientate_after:
            shift_rotations_to_end(normal_sequence, move_meta)

        for move in normal_sequence:
            if orientate_after and is_rotation(move):
                break
            permutation = permutation[permutations[move]]

    if invert_after:
        return invert(permutation)
    return permutation
