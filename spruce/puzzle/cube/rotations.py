"""Canonical representation of whole-cube rotations."""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Final

from spruce.algebra.permutation import get_identity
from spruce.puzzle.cube.geometry import create_permutations

if TYPE_CHECKING:
    from collections.abc import Sequence

    from spruce.algebra.group import MoveMeta
    from spruce.types import MoveSymbol


# State (X, Y) means original X face points Up and original Y face points Front
# Canonical solution: 0/1 directly, or rotate top face correctly, then front face
CANONICAL_ROTATION_SEQUENCES: Final[dict[tuple[int, int], str]] = {
    (0, 1): "",
    (0, 2): "y",
    (0, 3): "y2",
    (0, 4): "y'",
    (1, 0): "x y2",
    (1, 2): "x y",
    (1, 4): "x y'",
    (1, 5): "x",
    (2, 0): "z' y'",
    (2, 1): "z'",
    (2, 3): "z' y2",
    (2, 5): "z' y",
    (3, 0): "x'",
    (3, 2): "x' y",
    (3, 4): "x' y'",
    (3, 5): "x' y2",
    (4, 0): "z y",
    (4, 1): "z",
    (4, 3): "z y2",
    (4, 5): "z y'",
    (5, 1): "z2",
    (5, 2): "x2 y",
    (5, 3): "x2",
    (5, 4): "x2 y'",
}


# TODO: Implement the full Cayley table for rotation group
def canonicalize_rotations(
    rotations: Sequence[MoveSymbol],
    move_meta: MoveMeta,
) -> list[MoveSymbol]:
    """Get the canonical rotation representation from the sequence."""
    state = get_identity(size=6)
    permutations = create_permutations(cube_size=1)

    for rotation in rotations:
        state = state[permutations[rotation]]

    canonical = CANONICAL_ROTATION_SEQUENCES[(state[0], state[1])]

    return move_meta.to_word(canonical.split())
