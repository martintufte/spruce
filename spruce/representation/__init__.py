from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from typing import Final

from spruce.representation.utils import get_identity
from spruce.representation.utils import invert

if TYPE_CHECKING:
    from collections.abc import Iterable

    from spruce.move.meta import MoveMeta
    from spruce.move.sequence import MoveSequence
    from spruce.types import MoveSymbol
    from spruce.types import PermutationArray

LOGGER: Final = logging.getLogger(__name__)


def _substitute_moves(word: list[MoveSymbol], move_meta: MoveMeta) -> list[MoveSymbol]:
    """Return the word with substitutions applied, flattening multi-symbol expansions."""
    out: list[MoveSymbol] = []
    for symbol in word:
        new_symbols = move_meta.substitute(symbol)
        if isinstance(new_symbols, str):
            out.append(new_symbols)
        else:
            out.extend(new_symbols)
    return out


def _truncate_at_rotation(word: list[MoveSymbol], move_meta: MoveMeta) -> list[MoveSymbol]:
    """Return the word up to (excluding) the first rotation symbol."""
    for index, symbol in enumerate(word):
        if symbol in move_meta.rotation_symbols:
            return word[:index]
    return word


def _apply_moves(
    permutation: PermutationArray,
    word: Iterable[MoveSymbol],
    permutations: dict[MoveSymbol, PermutationArray],
) -> PermutationArray:
    """Compose the moves onto the permutation.

    Uses ndarray.take over fancy indexing as it is measurably faster for small arrays.
    """
    for symbol in word:
        permutation = permutation.take(permutations[symbol])
    return permutation


def get_rubiks_cube_permutation(
    sequence: MoveSequence,
    move_meta: MoveMeta,
    initial_permutation: PermutationArray | None = None,
    use_inverse: bool = True,
    orientate_after: bool = False,
    invert_after: bool = False,
) -> PermutationArray:
    """Get the cube permutation from a move sequence.

    Args:
        sequence (MoveSequence): Move sequence.
        move_meta (MoveMeta): Meta information about moves.
        initial_permutation (PermutationArray, optional): Initial permutation. Defaults to None.
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
