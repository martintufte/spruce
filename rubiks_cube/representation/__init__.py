from __future__ import annotations

import copy
import logging
from typing import TYPE_CHECKING
from typing import Final

from rubiks_cube.move.sequence import replace_slice_moves
from rubiks_cube.move.sequence import replace_wide_moves
from rubiks_cube.move.sequence import shift_rotations_to_end
from rubiks_cube.representation.permutation import get_identity_permutation
from rubiks_cube.representation.utils import invert

if TYPE_CHECKING:
    from rubiks_cube.configuration.types import CubePermutation
    from rubiks_cube.move.meta import MoveMeta
    from rubiks_cube.move.sequence import MoveSequence

LOGGER: Final = logging.getLogger(__name__)


def get_rubiks_cube_permutation(
    sequence: MoveSequence,
    move_meta: MoveMeta,
    initial_permutation: CubePermutation | None = None,
    use_inverse: bool = True,
    orientate_after: bool = False,
    invert_after: bool = False,
) -> CubePermutation:
    """Get the cube permutation from a sequence of moves.

    Args:
        sequence (MoveSequence): Rubiks cube move sequence.
        move_meta (MoveMeta): Meta information about moves.
        initial_permutation (CubePermutation, optional): Initial permutation of the cube.
        use_inverse (bool, optional): Use the inverse part. Defaults to True.
        orientate_after (bool, optional): Orientate to same orientation as the
            initial permutation. Defaults to False.
        invert_after (bool, optional): Whether to invert after applying moves. Defaults to False.

    Returns:
        CubePermutation: The Rubiks cube permutation.
    """
    sequence = copy.deepcopy(sequence)
    permutations = move_meta.permutations

    # Create permutation
    if initial_permutation is not None:
        assert initial_permutation.size == 6 * move_meta.cube_size**2
        permutation = initial_permutation.copy()
    else:
        permutation = get_identity_permutation(cube_size=move_meta.cube_size)

    # Substitute moves that rotate the cube with normal moves
    replace_wide_moves(sequence, move_meta)
    replace_slice_moves(sequence, move_meta)

    # Shift rotations to the end if orientate after
    if orientate_after:
        shift_rotations_to_end(sequence, move_meta)

    # Apply moves on inverse
    if use_inverse and sequence.inverse:
        inverted_permutation = invert(permutation)
        for move in sequence.inverse:
            if orientate_after and move_meta.is_rotation(move):
                break
            inverted_permutation = inverted_permutation[permutations[move]]
        permutation = invert(inverted_permutation)

    # Apply moves on normal
    if sequence.normal:
        for move in sequence.normal:
            if orientate_after and move_meta.is_rotation(move):
                break
            permutation = permutation[permutations[move]]

    if invert_after:
        return invert(permutation)
    return permutation
