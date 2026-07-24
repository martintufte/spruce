from __future__ import annotations

import re
from functools import cached_property
from functools import lru_cache
from typing import TYPE_CHECKING
from typing import Any
from typing import Final

import attrs
import numpy as np

from spruce.configuration.enumeration import Puzzle  # noqa: TC001
from spruce.configuration.regex import IDENTITY_SEARCH
from spruce.configuration.regex import ROTATION_SEARCH
from spruce.configuration.regex import SLICE_PATTERN
from spruce.configuration.regex import SLICE_SEARCH
from spruce.configuration.regex import WIDE_PATTERN
from spruce.configuration.regex import WIDE_SEARCH
from spruce.move.actions import expanded_to_available_permutations
from spruce.representation.permutation import create_permutations
from spruce.representation.utils import get_identity
from spruce.representation.utils import invert
from spruce.types import PermutationClassification

if TYPE_CHECKING:
    from collections.abc import Sequence
    from collections.abc import Set as AbstractSet

    from spruce.types import PermutationArray


# TODO: Consider removing hardcoded slice substitutions
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
            return match.group(0)

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
    state = get_identity(size=6)
    permutations = create_permutations(cube_size=1)

    for rotation in rotations:
        state = state[permutations[rotation]]

    return CANONICAL_ROTATION_SEQUENCES[(state[0], state[1])]


@attrs.frozen
class MoveMeta:
    permutations: dict[str, PermutationArray]
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

    puzzle: Puzzle

    def get_actions(
        self,
        generator: AbstractSet[str],
        expand: bool = True,
    ) -> dict[str, PermutationArray]:
        """Build the action map for a set of move symbols using this cube's move metadata.

        Each symbol in the generator must be a key of ``permutations``.
        TODO: Represent algorithms (multi-move sequences) in MoveMeta as well.
        """
        actions: dict[str, PermutationArray] = {}
        for symbol in generator:
            permutation = self.permutations.get(symbol)
            if permutation is None:
                raise ValueError(f"Unknown move symbol {symbol!r}, not found in permutations")
            actions[symbol] = permutation
            if expand:
                actions.update(
                    expanded_to_available_permutations(
                        permutation,
                        available_permutations=self.permutations,
                    ),
                )
        return actions

    @cached_property
    def pieces(self) -> list[set[int]]:
        """Find blocks of imprimitivity that always moves together as a unit."""
        identity = np.arange(self.size, dtype=self.dtype)

        # Only include base moves that don't substitute
        base_moves = self.base_moves - set(self.substitutions)

        # Restrict to indices that are affected
        affected_by_move = {
            move: {int(i) for i in np.flatnonzero(self.permutations[move] != identity)}
            for move in base_moves
        }

        # Iteratively find blocks of imprimitivity
        piece_subsets: list[set[int]] = [set().union(*affected_by_move.values())]

        for affected in affected_by_move.values():

            new_piece_subsets: list[set[int]] = []
            for subset in piece_subsets:
                if affected_subset := subset & affected:
                    new_piece_subsets.append(affected_subset)
                if unaffected_subset := subset - affected:
                    new_piece_subsets.append(unaffected_subset)

            piece_subsets = new_piece_subsets

        return piece_subsets

    @cached_property
    def has_parity(self) -> bool:
        """Check if the permutations has parity.

        Checks if there exists any permutation that has odd transposition decomposition.
        It is checked by counting the number of piece cycles (including 1-cycles)
        of every permutation. If the difference between the number of pieces and the
        number of cycles is 1 (mod 2), then the permutation is odd.
        """
        piece_subsets = self.pieces
        n_pieces = len(piece_subsets)
        base_moves = self.base_moves - set(self.substitutions)

        def is_odd(permutation: PermutationArray) -> bool:
            visited: set[int] = set()
            cycles = 0

            for subset in piece_subsets:
                if any(idx in visited for idx in subset):
                    continue

                cycles += 1
                idx = next(iter(subset))
                while idx not in visited:
                    visited.add(idx)
                    idx = permutation[idx]

            return (n_pieces - cycles) % 2 == 1

        return any(is_odd(self.permutations[move]) for move in base_moves)

    @classmethod
    @lru_cache(maxsize=10)
    def from_puzzle(cls, puzzle: Puzzle) -> MoveMeta:
        # Create all permutations given the puzzle
        cube_size = puzzle.cube_size
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
            puzzle=puzzle,
        )

    @classmethod
    def from_permutations(
        cls,
        permutations: dict[str, PermutationArray],
        classifications: dict[str, PermutationClassification],
        puzzle: Puzzle,
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
                f"Missing keys: {missing_classification_keys}",
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

        # Batch-compose all pairs of base moves at once. Row b of perm_a.take(stacked) is
        # perm_a[perm_b], so composed_bytes[a][b] holds the serialized composition of every pair.
        base_list = list(base_moves)
        stacked = np.array([perm_by_move[move] for move in base_list])
        state_size = size * dtype.itemsize

        def split_states(raw: bytes) -> list[bytes]:
            return [raw[i * state_size : (i + 1) * state_size] for i in range(len(base_list))]

        composed_bytes = [split_states(perm_by_move[a].take(stacked).tobytes()) for a in base_list]

        # Look at all pairs of legal moves for composition, commutativity and inversion
        compose: dict[tuple[str, str], str] = {}
        commutes: dict[str, set[str]] = {move: set() for move in base_moves}
        inverse_map: dict[str, str] = {}
        conjugation_map: dict[tuple[str, str], str] = {}

        for a_index, move_a in enumerate(base_list):
            row = composed_bytes[a_index]
            for b_index, move_b in enumerate(base_list):
                ab_bytes = row[b_index]

                if ab_bytes == identity_bytes:
                    compose[(move_a, move_b)] = ""
                    inverse_map[move_a] = move_b
                elif ab_bytes in move_by_perm_bytes:
                    compose[(move_a, move_b)] = move_by_perm_bytes[ab_bytes]

                # Compositions are equal iff their serializations are equal
                if ab_bytes == composed_bytes[b_index][a_index]:
                    commutes[move_a].add(move_b)

        # Populate the conjugation map with rotations, batched over all base moves
        for rot in rotation_moves:
            perm_rot = rotation_by_move[rot]
            conjugated = perm_rot.take(stacked)[:, invert(perm_rot)]
            conjugated_by_move = zip(base_list, split_states(conjugated.tobytes()), strict=True)
            for move_a, conjugated_bytes in conjugated_by_move:
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
            puzzle=puzzle,
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
