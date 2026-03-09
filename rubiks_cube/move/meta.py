from __future__ import annotations

import re
from dataclasses import dataclass
from functools import cached_property
from functools import lru_cache
from typing import TYPE_CHECKING
from typing import ClassVar
from typing import Final
from typing import Sequence

import numpy as np

from rubiks_cube.configuration.regex import ROTATION_SEARCH
from rubiks_cube.representation.permutation import create_permutations
from rubiks_cube.representation.permutation import get_identity_permutation
from rubiks_cube.representation.utils import conjugate
from rubiks_cube.representation.utils import invert

if TYPE_CHECKING:
    from rubiks_cube.configuration.types import CubePermutation


# TODO: Consider removing hardcoded slice subsitituition
SLICE_MAPPING: Final[dict[str, tuple[str, str, str]]] = {
    "M": ("L'", "R", "x'"),
    "E": ("U", "D'", "y'"),
    "S": ("F'", "B", "z"),
}


# TODO: Consider removing hardcoded wide subsitituition
WIDE_MAPPING: Final[dict[str, tuple[str, str, str]]] = {
    "L": ("R", "x", "'"),
    "R": ("L", "x", ""),
    "F": ("B", "z", ""),
    "B": ("F", "z", "'"),
    "U": ("D", "y", ""),
    "D": ("U", "y", "'"),
}


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


# TODO: Implement the full Cayley table for rotation group
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

    # Grouping
    rotation_moves: set[str]
    legal_moves: set[str]

    # Algebraic properties
    compose: dict[tuple[str, str], str]
    commutes: dict[str, set[str]]
    inverse_map: dict[str, str]
    conjugation_map: dict[tuple[str, str], str]

    # Hardcoded properties
    slice_mapping: ClassVar = SLICE_MAPPING
    wide_mapping: ClassVar = WIDE_MAPPING

    @property
    def size(self) -> int:
        """Size of the permutations."""
        return 6 * self.cube_size**2

    def discover_pieces(self) -> list[set[int]]:
        """Automatically discover and classifies groups of indices forming 'pieces'.

        A 'piece' is a group of indices where all of them are either affected
        or stay unaffected by every permutation.
        """
        piece_groups: list[set[int]] = [set(range(self.size))]

        # Iteratively split the group into smaller groups
        identity = get_identity_permutation(self.cube_size)
        for permutation in self.permutations.values():
            affected: set[int] = set(np.where(identity != permutation)[0])

            new_piece_groups: list[set[int]] = []
            for group in piece_groups:
                if affected_group := group & affected:
                    new_piece_groups.append(affected_group)
                if unaffected_group := group - affected:
                    new_piece_groups.append(unaffected_group)

            piece_groups = new_piece_groups

        return piece_groups

    @cached_property
    def has_parity(self) -> bool:
        """Check if the cube has parity.

        Checks if there exists any permutation has odd transposition decomposition.
        It is checked by counting the number of piece cycles (including 1-cycles)
        of every permutation. If the difference between the number of pieces and the
        number of cycles is 1 (mod 2), then the permutation is odd.
        """
        piece_groups = self.discover_pieces()
        n_pieces = len(piece_groups)

        def is_odd(permutation: CubePermutation) -> bool:
            visited: set[int] = set()
            cycles = 0

            for group in piece_groups:
                if any(idx in visited for idx in group):
                    continue

                cycles += 1
                idx = next(iter(group))
                while idx not in visited:
                    visited.add(idx)
                    idx = permutation[idx]

            return (n_pieces - cycles) % 2 == 1

        return any(is_odd(permutation) for permutation in self.permutations.values())

    @classmethod
    @lru_cache(maxsize=10)
    def from_cube_size(cls, cube_size: int) -> MoveMeta:
        """Build MoveMeta for a given cube size."""
        permutations = create_permutations(cube_size=cube_size)
        identity_bytes = permutations["I"].tobytes()

        # Group move types
        rotation_moves = {move for move in permutations if bool(re.search(ROTATION_SEARCH, move))}
        legal_moves = {move for move in permutations if move != "I" and move not in rotation_moves}

        # Pre-compute bytes
        perm_by_move = {move: permutations[move] for move in legal_moves}
        move_by_perm_bytes = {perm_by_move[move].tobytes(): move for move in legal_moves}
        rotation_by_move = {rot: permutations[rot] for rot in rotation_moves}
        rotation_by_perm_bytes = {rotation_by_move[rot].tobytes(): rot for rot in rotation_moves}

        # Look at all pairs of legal moves for composition, cummutativity and inversion
        compose: dict[tuple[str, str], str] = {}
        commutes: dict[str, set[str]] = {move: set() for move in legal_moves}
        inverse_map: dict[str, str] = {}
        conjugation_map: dict[tuple[str, str], str] = {}

        for move_a in legal_moves:
            perm_a = perm_by_move[move_a]
            for move_b in legal_moves:
                perm_b = perm_by_move[move_b]
                composed = perm_a[perm_b]
                composed_bytes = composed.tobytes()

                if composed_bytes == identity_bytes:
                    compose[(move_a, move_b)] = ""
                    inverse_map[move_a] = move_b
                elif composed_bytes in move_by_perm_bytes:
                    compose[(move_a, move_b)] = move_by_perm_bytes[composed_bytes]

                if (perm_a[perm_b] == perm_b[perm_a]).all():
                    commutes[move_a].add(move_b)

            # Populate the conjugation map with rotations
            for rot in rotation_moves:
                perm_rot = rotation_by_move[rot]
                conjugated_bytes = conjugate(perm_a, perm_rot).tobytes()
                if conjugated_bytes in move_by_perm_bytes:
                    conjugation_map[(move_a, rot)] = move_by_perm_bytes[conjugated_bytes]

        # Update inversion map with rotation moves
        for rot in rotation_moves:
            inv_perm_bytes = invert(rotation_by_move[rot]).tobytes()
            if inv_perm_bytes in rotation_by_perm_bytes:
                inverse_map[rot] = rotation_by_perm_bytes[inv_perm_bytes]

        return cls(
            cube_size=cube_size,
            permutations=permutations,
            rotation_moves=rotation_moves,
            legal_moves=legal_moves,
            compose=compose,
            commutes=commutes,
            inverse_map=inverse_map,
            conjugation_map=conjugation_map,
        )

    def get_canonical_rotation(self, rotations: list[str]) -> list[str]:
        """Return the canonical representation of the rotation group."""
        assert all(move in self.rotation_moves for move in rotations)

        return canonicalize_rotations(rotations=rotations)

    def is_rotation(self, move: str) -> bool:
        """Return whether the move is a rotation."""
        return move in self.rotation_moves

    def is_invertible(self, move: str) -> bool:
        """Return whether the move is invertible."""
        return move in self.inverse_map

    def invert(self, moves: list[str]) -> list[str]:
        """Inverts the moves by reverting the list and mapping to inverse moves."""
        assert all(self.is_invertible(move) for move in moves)

        return [self.inverse_map[move] for move in reversed(moves)]

    def rotate(self, move: str, rotation: str) -> str:
        """Apply a rotatation of the move by mapping it to the new move."""
        assert move in self.legal_moves
        assert rotation in self.rotation_moves

        return self.conjugation_map[(move, rotation)]
