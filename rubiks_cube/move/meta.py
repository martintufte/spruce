from __future__ import annotations

import re
from functools import cached_property
from functools import lru_cache
from math import sqrt
from typing import TYPE_CHECKING
from typing import Any
from typing import Final
from typing import Sequence
from typing import cast

import attrs
import numpy as np

from rubiks_cube.configuration.regex import IDENTITY_SEARCH
from rubiks_cube.configuration.regex import ROTATION_SEARCH
from rubiks_cube.configuration.regex import SLICE_PATTERN
from rubiks_cube.configuration.regex import SLICE_SEARCH
from rubiks_cube.configuration.regex import WIDE_PATTERN
from rubiks_cube.configuration.regex import WIDE_SEARCH
from rubiks_cube.configuration.types import PermutationClassification
from rubiks_cube.representation.permutation import create_permutations
from rubiks_cube.representation.permutation import get_identity_permutation
from rubiks_cube.representation.utils import conjugate
from rubiks_cube.representation.utils import invert

if TYPE_CHECKING:
    from rubiks_cube.configuration.types import CubePermutation


# TODO: Consider removing hardcoded slice substitution
def substitute_slice_move(move: str) -> str:
    """Substitute the slice move."""
    slice_mapping: dict[str, tuple[str, str, str]] = {
        "M": ("L'", "R", "x'"),
        "E": ("U", "D'", "y'"),
        "S": ("F'", "B", "z"),
    }

    def replace_match(match: re.Match[Any]) -> str:
        slice = match.group(1)
        turn_mod = match.group(2)
        first, second, rot = slice_mapping[slice]

        combined = f"{first}{turn_mod} {second}{turn_mod} {rot}{turn_mod}"
        return combined.replace("''", "").replace("'2", "2")

    return SLICE_PATTERN.sub(replace_match, move)


# TODO: Consider removing hardcoded wide substitution
def substitute_wide_move(move: str, cube_size: int) -> str:
    """Substitute the wide notation if wider than cube_size/2."""
    wide_mapping: dict[str, tuple[str, str, str]] = {
        "L": ("R", "x", "'"),
        "R": ("L", "x", ""),
        "F": ("B", "z", ""),
        "B": ("F", "z", "'"),
        "U": ("D", "y", ""),
        "D": ("U", "y", "'"),
    }

    def replace_match(match: re.Match[Any]) -> str:
        wide = match.group(1) or "2"
        diff = cube_size - int(wide)
        if diff >= cube_size / 2:
            return cast("str", match.string)

        wide_mod = "w" if diff > 1 else ""
        diff_mod = str(diff) if diff > 2 else ""
        turn_mod = match.group(3)
        move = match.group(2)
        base, rot, rot_mod = wide_mapping[move]
        rot_mod = f"{rot_mod}{turn_mod}".replace("''", "").replace("'2", "2")

        if diff < 1:
            return f"{rot}{rot_mod}"
        return f"{diff_mod}{base}{wide_mod}{turn_mod} {rot}{rot_mod}"

    return WIDE_PATTERN.sub(replace_match, move)


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
def _canonicalize_rotations(rotations: Sequence[str]) -> list[str]:
    """Get the canonical rotation representation from the sequence."""
    state = get_identity_permutation(cube_size=1)
    permutations = create_permutations(cube_size=1)

    for rotation in rotations:
        state = state[permutations[rotation]]

    return CANONICAL_ROTATION_SEQUENCES[(state[0], state[1])]


@attrs.frozen
class MoveMeta:
    permutations: dict[str, CubePermutation]
    size: int
    dtype: np.dtype

    # Classification
    base_moves: set[str]
    rotation_moves: set[str]

    # Algebraic properties
    compose: dict[tuple[str, str], str]
    commutes: dict[str, set[str]]
    inverse_map: dict[str, str]
    conjugation_map: dict[tuple[str, str], str]
    substitutions: dict[str, tuple[str, ...]]

    @cached_property
    def cube_size(self) -> int:
        return round(sqrt(self.size / 6))

    @cached_property
    def pieces(self) -> list[set[int]]:
        """A 'piece' is a set of indices where all of them are either affected
        or stay unaffected by every permutation.

        TODO: Check that a piece 'fixate' another piece, so 3x3 don't have 3 center pieces.
        """
        piece_groups: list[set[int]] = [set(range(self.size))]

        # Iteratively split the group into smaller groups
        identity = np.arange(self.size, dtype=self.dtype)

        for permutation in self.permutations.values():
            affected = {idx for idx, value in enumerate(identity != permutation) if value}

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
        """Check if the permutations has parity.

        Checks if there exists any permutation has odd transposition decomposition.
        It is checked by counting the number of piece cycles (including 1-cycles)
        of every permutation. If the difference between the number of pieces and the
        number of cycles is 1 (mod 2), then the permutation is odd.
        """
        piece_groups = self.pieces
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
        # Create all permutations
        permutations = create_permutations(cube_size=cube_size)

        # Classify the cube permutations and add substitutions
        classifications: dict[str, PermutationClassification] = {}
        substitutions: dict[str, tuple[str, ...]] = {}
        for move in permutations:
            if re.search(IDENTITY_SEARCH, move) is not None:
                classifications[move] = PermutationClassification.IDENTITY

            elif re.search(ROTATION_SEARCH, move) is not None:
                classifications[move] = PermutationClassification.ROTATION

            elif re.search(SLICE_SEARCH, move) is not None:
                classifications[move] = PermutationClassification.BASE
                substituted = substitute_slice_move(move)
                if substituted != move:
                    substitutions[move] = tuple(substituted.split())

            elif re.search(WIDE_SEARCH, move) is not None:
                classifications[move] = PermutationClassification.BASE
                substituted = substitute_wide_move(move, cube_size=cube_size)
                if substituted != move:
                    substitutions[move] = tuple(substituted.split())

            else:
                classifications[move] = PermutationClassification.BASE

        return cls.from_permutations(
            permutations=permutations,
            classifications=classifications,
            substitutions=substitutions,
        )

    @classmethod
    def from_permutations(
        cls,
        permutations: dict[str, CubePermutation],
        classifications: dict[str, PermutationClassification],
        substitutions: dict[str, tuple[str, ...]] | None = None,
    ) -> MoveMeta:
        """Build the permutation meta using the provided permutations."""
        # Check that all moves have classification and same size and dtype
        if len(permutations) == 0:
            raise ValueError("Permutations must be non-empty")
        missing_classification_keys = [move for move in permutations if move not in classifications]
        if missing_classification_keys:
            raise ValueError(
                "Classifications must contain all permutation keys. "
                f"Missing keys: {missing_classification_keys}"
            )

        # Check consistency with sizes and dtypes
        first_permutation = next(iter(permutations.values()))
        size = first_permutation.size
        dtype = first_permutation.dtype
        if any(permutation.size != size for permutation in permutations.values()):
            raise ValueError("All permutations must have the same size")
        if any(permutation.dtype != dtype for permutation in permutations.values()):
            raise ValueError("All permutations must have the same dtype")

        # Create identity permutation
        identity = np.arange(size, dtype=dtype)
        identity_bytes = identity.tobytes()

        # Classify the permutations
        base_moves = {
            move for move in permutations if classifications[move] is PermutationClassification.BASE
        }
        rotation_moves = {
            move
            for move in permutations
            if classifications[move] is PermutationClassification.ROTATION
        }

        # Pre-compute bytes
        perm_by_move = {move: permutations[move] for move in base_moves}
        move_by_perm_bytes = {perm_by_move[move].tobytes(): move for move in base_moves}
        rotation_by_move = {rot: permutations[rot] for rot in rotation_moves}
        rotation_by_perm_bytes = {rotation_by_move[rot].tobytes(): rot for rot in rotation_moves}

        # Look at all pairs of legal moves for composition, cummutativity and inversion
        compose: dict[tuple[str, str], str] = {}
        commutes: dict[str, set[str]] = {move: set() for move in base_moves}
        inverse_map: dict[str, str] = {}
        conjugation_map: dict[tuple[str, str], str] = {}

        for move_a in base_moves:
            perm_a = perm_by_move[move_a]
            for move_b in base_moves:
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

        if substitutions is None:
            substitutions = {}

        return cls(
            permutations=permutations,
            size=size,
            dtype=dtype,
            rotation_moves=rotation_moves,
            base_moves=base_moves,
            compose=compose,
            commutes=commutes,
            inverse_map=inverse_map,
            conjugation_map=conjugation_map,
            substitutions=substitutions,
        )

    def invert(self, word: Sequence[str]) -> list[str]:
        """Inverts the word by reverting the order and mapping every move to its inverse."""
        if not all(move in self.inverse_map for move in word):
            raise ValueError(f"Cannot invert {word!r}")

        return [self.inverse_map[move] for move in reversed(word)]

    def substitute(self, move: str) -> str | tuple[str, ...]:
        """Substitute the move with a sequence of moves."""
        return self.substitutions.get(move, move)

    def reduce(self, word: Sequence[str]) -> list[str]:
        """Find the reduced form of the word by cancellations."""

        def reduce_segment(word: list[str]) -> list[str]:
            """Reduce a rotation-free segment by commuting and combining closed moves."""
            stack: list[str] = []
            for move in word:
                stack.append(move)
                if move not in self.base_moves:
                    continue
                while stack:
                    current = stack[-1]
                    if current not in self.base_moves:
                        break
                    combined_pos: int | None = None
                    combined_move: str | None = None
                    for pos in range(len(stack) - 2, -1, -1):
                        previous = stack[pos]
                        if previous not in self.base_moves:
                            break
                        if not all(
                            between in self.commutes[previous] for between in stack[pos + 1 : -1]
                        ):
                            continue
                        combined = self.compose.get((previous, current))
                        if combined is not None:
                            combined_pos = pos
                            combined_move = combined
                            break
                    if combined_pos is None:
                        break
                    stack.pop()
                    del stack[combined_pos]
                    if combined_move:
                        stack.append(combined_move)
            return stack

        output: list[str] = []
        segment: list[str] = []
        for move in word:
            if move in self.rotation_moves:
                if segment:
                    output.extend(reduce_segment(segment))
                    segment = []
                output.append(move)
                continue
            segment.append(move)

        if segment:
            output.extend(reduce_segment(segment))

        return output

    def shift_rotations_to_end(self, word: Sequence[str], canonicalize: bool) -> list[str]:
        """Shift the rotations to the end of the word."""
        output_word: list[str] = []
        output_rotations: list[str] = []

        for move in word:
            if move in self.rotation_moves:
                output_rotations.append(move)
            else:
                rotated_move = move
                for rotation in reversed(output_rotations):
                    if (rotated_move, rotation) not in self.conjugation_map:
                        raise ValueError(f"No conjugation map for ({move!r}, {rotation!r})")
                    rotated_move = self.conjugation_map[(rotated_move, rotation)]
                output_word.append(rotated_move)

        if canonicalize:
            return output_word + _canonicalize_rotations(output_rotations)
        return output_word + output_rotations
