from __future__ import annotations

import copy
import logging
from typing import TYPE_CHECKING
from typing import Final

from rubiks_cube.move.sequence import shift_rotations_to_end
from rubiks_cube.representation.permutation import get_identity_permutation
from rubiks_cube.representation.utils import invert

if TYPE_CHECKING:
    from rubiks_cube.configuration.types import PermutationArray
    from rubiks_cube.move.meta import MoveMeta
    from rubiks_cube.move.sequence import MoveSequence

LOGGER: Final = logging.getLogger(__name__)


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
    sequence = copy.deepcopy(sequence)
    permutations = move_meta.permutations

    # Create permutation
    if initial_permutation is not None:
        assert initial_permutation.size == 6 * move_meta.cube_size**2
        permutation = initial_permutation.copy()
    else:
        permutation = get_identity_permutation(cube_size=move_meta.cube_size)

    # Shift rotations to the end if orientate after
    if orientate_after:
        sequence.apply(move_meta.substitute)
        shift_rotations_to_end(sequence, move_meta, canonicalize=False)

    # Apply moves on inverse
    if use_inverse and sequence.inverse:
        inverted_permutation = invert(permutation)
        for move in sequence.inverse:
            if orientate_after and move in move_meta.rotation_moves:
                break
            inverted_permutation = inverted_permutation[permutations[move]]
        permutation = invert(inverted_permutation)

    # Apply moves on normal
    if sequence.normal:
        for move in sequence.normal:
            if orientate_after and move in move_meta.rotation_moves:
                break
            permutation = permutation[permutations[move]]

    if invert_after:
        return invert(permutation)
    return permutation
