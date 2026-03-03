from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import TYPE_CHECKING
from typing import Final
from typing import Sequence

from rubiks_cube.move.utils import is_rotation
from rubiks_cube.representation.permutation import create_permutations
from rubiks_cube.representation.permutation import get_identity_permutation
from rubiks_cube.representation.utils import get_identity

if TYPE_CHECKING:
    from rubiks_cube.configuration.types import CubePermutation


# State (X, Y) means original X face points Up and original Y face points Front
# Canonical solution: 0/1 directly, or rotate top face correctly, then front face
CANONICAL_ROTATION_SEQUENCES: Final[dict[tuple[int, int], list[str]]] = {
    (0, 1): [],
    (0, 2): ["y"],
    (0, 3): ["y2"],
    (0, 4): ["y'"],
    (1, 0): ["x", "y2"],
    (1, 2): ["x", "y"],
    (1, 4): ["x", "y'"],
    (1, 5): ["x"],
    (2, 0): ["z'", "y'"],
    (2, 1): ["z'"],
    (2, 3): ["z'", "y2"],
    (2, 5): ["z'", "y"],
    (3, 0): ["x'"],
    (3, 2): ["x'", "y"],
    (3, 4): ["x'", "y'"],
    (3, 5): ["x'", "y2"],
    (4, 0): ["z", "y"],
    (4, 1): ["z"],
    (4, 3): ["z", "y2"],
    (4, 5): ["z", "y'"],
    (5, 1): ["z2"],
    (5, 2): ["x2", "y"],
    (5, 3): ["x2"],
    (5, 4): ["x2", "y'"],
}


# TODO(martin): Consider implementing the full Cayley table
def canonicalize_rotations(rotations: Sequence[str]) -> list[str]:
    """Get the canonical rotation representation from the sequence."""
    state = get_identity_permutation(cube_size=1)
    permutations = create_permutations(cube_size=1)

    for rotation in rotations:
        state = state[permutations[rotation]]

    return CANONICAL_ROTATION_SEQUENCES[(state[0], state[1])]


@dataclass(frozen=True)
class MoveMeta:
    """Meta information about moves and their permutations.

    This class should capture all move-specific operations.
    """

    cube_size: int
    permutations: dict[str, CubePermutation]

    # Properties
    rotation_moves: set[str]
    legal_moves: set[str]
    compose: dict[tuple[str, str], str]
    commutes: dict[str, set[str]]

    @property
    def size(self) -> int:
        """Size of the permutations."""
        return 6 * self.cube_size**2

    def get_identity_permutation(self) -> CubePermutation:
        """Return the identity permutation."""
        return get_identity(size=self.size)

    @classmethod
    @lru_cache(maxsize=10)
    def from_cube_size(cls, cube_size: int) -> MoveMeta:
        """Build MoveMeta for a given cube size."""
        permutations = create_permutations(cube_size=cube_size)
        identity_bytes = permutations["I"].tobytes()

        rotation_moves = {move for move in permutations if is_rotation(move)}
        legal_moves = {move for move in permutations if move != "I" and move not in rotation_moves}
        perm_by_move = {move: permutations[move] for move in legal_moves}
        move_by_perm_bytes = {perm_by_move[move].tobytes(): move for move in legal_moves}

        compose: dict[tuple[str, str], str] = {}
        commutes: dict[str, set[str]] = {move: set() for move in legal_moves}

        for move_a in legal_moves:
            perm_a = perm_by_move[move_a]
            for move_b in legal_moves:
                perm_b = perm_by_move[move_b]
                composed = perm_a[perm_b]
                composed_bytes = composed.tobytes()

                if composed_bytes == identity_bytes:
                    compose[(move_a, move_b)] = ""
                elif composed_bytes in move_by_perm_bytes:
                    compose[(move_a, move_b)] = move_by_perm_bytes[composed_bytes]

                if (perm_a[perm_b] == perm_b[perm_a]).all():
                    commutes[move_a].add(move_b)

        return cls(
            cube_size=cube_size,
            permutations=permutations,
            rotation_moves=rotation_moves,
            legal_moves=legal_moves,
            compose=compose,
            commutes=commutes,
        )

    def canonicalize_rotations(self, rotations: list[str]) -> list[str]:
        return canonicalize_rotations(rotations=rotations)
