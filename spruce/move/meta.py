from __future__ import annotations

import re
from functools import cached_property
from functools import lru_cache
from typing import TYPE_CHECKING
from typing import Any
from typing import Final

import attrs
import numpy as np

from spruce.configuration.enumeration import Puzzle
from spruce.configuration.regex import IDENTITY_SEARCH
from spruce.configuration.regex import ROTATION_SEARCH
from spruce.configuration.regex import SLICE_PATTERN
from spruce.configuration.regex import SLICE_SEARCH
from spruce.configuration.regex import WIDE_PATTERN
from spruce.configuration.regex import WIDE_SEARCH
from spruce.configuration.regex import canonical_key
from spruce.move.sequence import MoveSequence
from spruce.representation.permutation import create_permutations
from spruce.representation.utils import get_identity
from spruce.representation.utils import invert
from spruce.types import MoveSymbol
from spruce.types import PermutationClassification

if TYPE_CHECKING:
    from collections.abc import Iterable
    from collections.abc import Sequence
    from collections.abc import Set as AbstractSet

    from spruce.types import PermutationArray


# TODO: Consider removing hardcoded slice substitutions
def substitute_slice_move(symbol: MoveSymbol) -> tuple[MoveSymbol, ...]:
    """Substitute the slice symbol, returning the word it expands to."""
    # Keyed by the bare slice letter; the parts are glued to a turn modifier below,
    # so they are notation fragments rather than standalone move symbols.
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

    substituted = SLICE_PATTERN.sub(replace_match, symbol)

    return tuple(MoveSymbol(part) for part in substituted.split())


# TODO: Consider removing hardcoded wide substitution
def substitute_wide_move(symbol: MoveSymbol, cube_size: int) -> tuple[MoveSymbol, ...]:
    """Substitute the wide notation if wider than cube_size/2, as the word it expands to."""
    # Keyed by the bare face letter; the parts are glued to width and turn modifiers
    # below, so they are notation fragments rather than standalone move symbols.
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

    substituted = WIDE_PATTERN.sub(replace_match, symbol)

    return tuple(MoveSymbol(part) for part in substituted.split())


DEFAULT_GENERATOR_BY_PUZZLE: Final[dict[Puzzle, tuple[str, ...]]] = {
    Puzzle._2x2x2: ("U", "R", "F"),
    Puzzle._3x3x3: ("U", "D", "L", "R", "F", "B"),
    Puzzle._4x4x4: ("U", "Uw", "D", "L", "R", "Rw", "F", "Fw", "B"),
}


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


def _expanded_to_available_permutations(
    permutation: PermutationArray,
    available_permutations: dict[MoveSymbol, PermutationArray],
) -> dict[MoveSymbol, PermutationArray]:
    """Expand a permutation by matching repeated powers to known actions."""
    identity_bytes = np.arange(permutation.size, dtype=permutation.dtype).tobytes()
    symbol_by_perm_bytes = {perm.tobytes(): name for name, perm in available_permutations.items()}
    expanded_actions: dict[MoveSymbol, PermutationArray] = {}
    current_permutation = permutation

    while True:
        current_permutation = current_permutation.take(permutation)
        current_bytes = current_permutation.tobytes()
        if current_bytes == identity_bytes:
            break
        symbol = symbol_by_perm_bytes.get(current_bytes)
        if symbol is None:
            break
        expanded_actions[symbol] = available_permutations[symbol]

    return expanded_actions


@attrs.frozen
class MoveMeta:
    permutations: dict[MoveSymbol, PermutationArray]
    size: int
    dtype: np.dtype

    # Classification
    base_symbols: set[MoveSymbol]
    rotation_symbols: set[MoveSymbol]

    # Algebraic properties
    compose: dict[tuple[MoveSymbol, MoveSymbol], MoveSymbol]
    commutes: dict[MoveSymbol, set[MoveSymbol]]
    inverse_map: dict[MoveSymbol, MoveSymbol]
    conjugation_map: dict[tuple[MoveSymbol, MoveSymbol], MoveSymbol]
    substitutions: dict[MoveSymbol, tuple[MoveSymbol, ...]]

    # Move order rank
    canonical_order: dict[MoveSymbol, int]

    puzzle: Puzzle

    @cached_property
    def symbols(self) -> frozenset[MoveSymbol]:
        return frozenset(self.permutations)

    def _reject_unknown(self, symbols: Iterable[str]) -> None:
        """Raise if any string is not a move symbol of this puzzle."""
        unknown = sorted(symbol for symbol in symbols if symbol not in self.symbols)
        if unknown:
            raise ValueError(f"Unknown move symbols {unknown} for puzzle {self.puzzle.value}")

    def to_symbols(self, *symbols: str) -> frozenset[MoveSymbol]:
        """Validate plain strings as a set of move symbols of this puzzle.

        Together with `to_word` and `to_sequence` this is the only supported way to turn
        strings into `MoveSymbol`s, so that no unvalidated symbol can enter the system.

        Raises:
            ValueError: If any string is not a move symbol of this puzzle.
        """
        self._reject_unknown(symbols)

        return frozenset(MoveSymbol(symbol) for symbol in symbols)

    def to_word(self, symbols: Iterable[str]) -> list[MoveSymbol]:
        """Validate plain strings as an ordered word of this puzzle.

        Raises:
            ValueError: If any string is not a move symbol of this puzzle.
        """
        word = list(symbols)
        self._reject_unknown(word)

        return [MoveSymbol(symbol) for symbol in word]

    def to_sequence(self, string: str) -> MoveSequence:
        """Parse a move sequence and validate its symbols against this puzzle.

        `MoveSequence.from_str` only checks that the notation is well formed; this also
        checks that every symbol exists for this puzzle.

        Raises:
            ValueError: If the string is not a well formed sequence of this puzzle.
        """
        sequence = MoveSequence.from_str(string)
        self._reject_unknown([*sequence.normal, *sequence.inverse])

        return sequence

    @cached_property
    def default_generator(self) -> frozenset[MoveSymbol]:
        """The generator used when the caller has no preference for this puzzle.

        Raises:
            ValueError: If no default generator is defined for this puzzle.
        """
        default = DEFAULT_GENERATOR_BY_PUZZLE.get(self.puzzle)
        if default is None:
            raise ValueError(f"No default generator defined for puzzle {self.puzzle.value}")
        return self.to_symbols(*default)

    def get_actions(
        self,
        generator: AbstractSet[MoveSymbol],
        expand: bool = True,
    ) -> dict[MoveSymbol, PermutationArray]:
        """Build the action map for a set of move symbols using this cube's move metadata.

        Each symbol in the generator must be a key of `permutations`.
        The returned actions are in canonical move order.
        TODO: Represent algorithms (multi-move sequences) in `MoveMeta` as well.
        """
        self._reject_unknown(generator)

        actions: dict[MoveSymbol, PermutationArray] = {}
        for symbol in generator:
            permutation = self.permutations[symbol]
            actions[symbol] = permutation
            if expand:
                actions.update(
                    _expanded_to_available_permutations(
                        permutation,
                        available_permutations=self.permutations,
                    ),
                )
        return {symbol: actions[symbol] for symbol in self.sorted(actions)}

    @cached_property
    def pieces(self) -> list[set[int]]:
        """Find blocks of imprimitivity that always moves together as a unit."""
        identity = np.arange(self.size, dtype=self.dtype)

        # Only include base symbols that don't substitute
        base_symbols = self.base_symbols - set(self.substitutions)

        # Restrict to indices that are affected
        affected_by_symbol = {
            symbol: {int(i) for i in np.flatnonzero(self.permutations[symbol] != identity)}
            for symbol in base_symbols
        }

        # Iteratively find blocks of imprimitivity
        piece_subsets: list[set[int]] = [set().union(*affected_by_symbol.values())]

        for affected in affected_by_symbol.values():
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
        base_symbols = self.base_symbols - set(self.substitutions)

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

        return any(is_odd(self.permutations[symbol]) for symbol in base_symbols)

    @classmethod
    @lru_cache(maxsize=10)
    def from_puzzle(cls, puzzle: Puzzle) -> MoveMeta:
        # Create all permutations given the puzzle
        cube_size = puzzle.cube_size
        permutations = create_permutations(cube_size=cube_size)

        # Classify the cube permutations and add substitutions
        classifications: dict[MoveSymbol, PermutationClassification] = {}
        substitutions: dict[MoveSymbol, tuple[MoveSymbol, ...]] = {}
        for symbol in permutations:
            if re.search(IDENTITY_SEARCH, symbol) is not None:
                classifications[symbol] = PermutationClassification.IDENTITY

            elif re.search(ROTATION_SEARCH, symbol) is not None:
                classifications[symbol] = PermutationClassification.ROTATION

            elif re.search(SLICE_SEARCH, symbol) is not None:
                classifications[symbol] = PermutationClassification.BASE
                substituted = substitute_slice_move(symbol)
                if substituted != (symbol,):
                    substitutions[symbol] = substituted

            elif re.search(WIDE_SEARCH, symbol) is not None:
                classifications[symbol] = PermutationClassification.BASE
                substituted = substitute_wide_move(symbol, cube_size=cube_size)
                if substituted != (symbol,):
                    substitutions[symbol] = substituted

            else:
                classifications[symbol] = PermutationClassification.BASE

        return cls.from_permutations(
            permutations=permutations,
            classifications=classifications,
            substitutions=substitutions,
            puzzle=puzzle,
        )

    @classmethod
    def from_permutations(
        cls,
        permutations: dict[MoveSymbol, PermutationArray],
        classifications: dict[MoveSymbol, PermutationClassification],
        puzzle: Puzzle,
        substitutions: dict[MoveSymbol, tuple[MoveSymbol, ...]] | None = None,
    ) -> MoveMeta:
        """Build the permutation meta using the provided permutations."""
        # Check that all symbols have classification and same size and dtype
        if len(permutations) == 0:
            raise ValueError("Permutations must be non-empty")
        missing_classification_keys = [
            symbol for symbol in permutations if symbol not in classifications
        ]
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
        base_symbols = {
            symbol
            for symbol in permutations
            if classifications[symbol] is PermutationClassification.BASE
        }
        rotation_symbols = {
            symbol
            for symbol in permutations
            if classifications[symbol] is PermutationClassification.ROTATION
        }

        # Pre-compute bytes
        perm_by_symbol = {symbol: permutations[symbol] for symbol in base_symbols}
        symbol_by_perm_bytes = {perm_by_symbol[symbol].tobytes(): symbol for symbol in base_symbols}
        rotation_by_symbol = {symbol: permutations[symbol] for symbol in rotation_symbols}
        rotation_by_perm_bytes = {
            rotation_by_symbol[symbol].tobytes(): symbol for symbol in rotation_symbols
        }

        # Batch-compose all pairs of base symbols at once. Row b of perm_a.take(stacked) is
        # perm_a[perm_b], so composed_bytes[a][b] holds the serialized composition of every pair.
        base_list = list(base_symbols)
        stacked = np.array([perm_by_symbol[symbol] for symbol in base_list])
        state_size = size * dtype.itemsize

        def split_states(raw: bytes) -> list[bytes]:
            return [raw[i * state_size : (i + 1) * state_size] for i in range(len(base_list))]

        composed_bytes = [
            split_states(perm_by_symbol[a].take(stacked).tobytes()) for a in base_list
        ]

        # Look at all pairs of legal symbols for composition, commutativity and inversion
        compose: dict[tuple[MoveSymbol, MoveSymbol], MoveSymbol] = {}
        commutes: dict[MoveSymbol, set[MoveSymbol]] = {symbol: set() for symbol in base_symbols}
        inverse_map: dict[MoveSymbol, MoveSymbol] = {}
        conjugation_map: dict[tuple[MoveSymbol, MoveSymbol], MoveSymbol] = {}

        for a_index, symbol_a in enumerate(base_list):
            row = composed_bytes[a_index]
            for b_index, symbol_b in enumerate(base_list):
                ab_bytes = row[b_index]

                if ab_bytes == identity_bytes:
                    compose[(symbol_a, symbol_b)] = MoveSymbol("")
                    inverse_map[symbol_a] = symbol_b
                elif ab_bytes in symbol_by_perm_bytes:
                    compose[(symbol_a, symbol_b)] = symbol_by_perm_bytes[ab_bytes]

                # Compositions are equal iff their serializations are equal
                if ab_bytes == composed_bytes[b_index][a_index]:
                    commutes[symbol_a].add(symbol_b)

        # Populate the conjugation map with rotations, batched over all base symbols
        for rot_symbol in rotation_symbols:
            perm_rot = rotation_by_symbol[rot_symbol]
            conjugated = perm_rot.take(stacked)[:, invert(perm_rot)]
            conjugated_by_symbol = zip(base_list, split_states(conjugated.tobytes()), strict=True)
            for symbol_a, conjugated_bytes in conjugated_by_symbol:
                if conjugated_bytes in symbol_by_perm_bytes:
                    conjugation_map[(symbol_a, rot_symbol)] = symbol_by_perm_bytes[conjugated_bytes]

        # Update inversion map with rotation symbols
        for rot_symbol in rotation_symbols:
            inv_perm_bytes = invert(rotation_by_symbol[rot_symbol]).tobytes()
            if inv_perm_bytes in rotation_by_perm_bytes:
                inverse_map[rot_symbol] = rotation_by_perm_bytes[inv_perm_bytes]

        if substitutions is None:
            substitutions = {}

        # Rank every symbol once so downstream sorting is a dict lookup
        def sort_key(symbol: MoveSymbol) -> tuple[int, ...]:
            try:
                return (0, *canonical_key(symbol))
            except ValueError:
                return (1, *(ord(char) for char in symbol))

        canonical_order = {
            symbol: rank for rank, symbol in enumerate(sorted(permutations, key=sort_key))
        }

        return cls(
            permutations=permutations,
            size=size,
            dtype=dtype,
            rotation_symbols=rotation_symbols,
            base_symbols=base_symbols,
            compose=compose,
            commutes=commutes,
            inverse_map=inverse_map,
            conjugation_map=conjugation_map,
            substitutions=substitutions,
            canonical_order=canonical_order,
            puzzle=puzzle,
        )

    def sorted(self, symbols: Iterable[MoveSymbol]) -> list[MoveSymbol]:
        """Sort the symbols in canonical order."""
        return sorted(symbols, key=self.canonical_order.__getitem__)

    def invert(self, word: Sequence[MoveSymbol]) -> list[MoveSymbol]:
        """Inverts the word by reverting the order and mapping every symbol to its inverse."""
        if not all(symbol in self.inverse_map for symbol in word):
            raise ValueError(f"Cannot invert {word!r}")

        return [self.inverse_map[symbol] for symbol in reversed(word)]

    def substitute(self, symbol: MoveSymbol) -> tuple[MoveSymbol, ...]:
        """Substitute the symbol with the word it expands to, or itself if no substitution."""
        return self.substitutions.get(symbol, (symbol,))

    def reduce(self, word: Sequence[MoveSymbol]) -> list[MoveSymbol]:
        """Find the reduced form of the word by cancellations."""

        def reduce_segment(word: list[MoveSymbol]) -> list[MoveSymbol]:
            """Reduce a rotation-free segment by commuting and combining closed symbols."""
            stack: list[MoveSymbol] = []
            for symbol in word:
                stack.append(symbol)
                if symbol not in self.base_symbols:
                    continue
                while stack:
                    current = stack[-1]
                    if current not in self.base_symbols:
                        break
                    combined_pos: int | None = None
                    combined_symbol: MoveSymbol | None = None
                    for pos in range(len(stack) - 2, -1, -1):
                        previous = stack[pos]
                        if previous not in self.base_symbols:
                            break
                        if not all(
                            between in self.commutes[previous] for between in stack[pos + 1 : -1]
                        ):
                            continue
                        combined = self.compose.get((previous, current))
                        if combined is not None:
                            combined_pos = pos
                            combined_symbol = combined
                            break
                    if combined_pos is None:
                        break
                    stack.pop()
                    del stack[combined_pos]
                    if combined_symbol:
                        stack.append(combined_symbol)
            return stack

        output: list[MoveSymbol] = []
        segment: list[MoveSymbol] = []
        for symbol in word:
            if symbol in self.rotation_symbols:
                if segment:
                    output.extend(reduce_segment(segment))
                    segment = []
                output.append(symbol)
                continue
            segment.append(symbol)

        if segment:
            output.extend(reduce_segment(segment))

        return output

    # TODO: Implement the full Cayley table for rotation group
    def _canonicalize_rotations(self, rotations: Sequence[MoveSymbol]) -> list[MoveSymbol]:
        """Get the canonical rotation representation from the sequence."""
        state = get_identity(size=6)
        permutations = create_permutations(cube_size=1)

        for rotation in rotations:
            state = state[permutations[rotation]]

        canonical = CANONICAL_ROTATION_SEQUENCES[(state[0], state[1])]

        return self.to_word(canonical.split())

    def shift_rotations_to_end(
        self,
        word: Sequence[MoveSymbol],
        canonicalize: bool,
    ) -> list[MoveSymbol]:
        """Shift the rotations to the end of the word."""
        output_word: list[MoveSymbol] = []
        output_rotations: list[MoveSymbol] = []

        for symbol in word:
            if symbol in self.rotation_symbols:
                output_rotations.append(symbol)
            else:
                rotated_symbol = symbol
                for rotation in reversed(output_rotations):
                    if (rotated_symbol, rotation) not in self.conjugation_map:
                        raise ValueError(f"No conjugation map for ({symbol!r}, {rotation!r})")
                    rotated_symbol = self.conjugation_map[(rotated_symbol, rotation)]
                output_word.append(rotated_symbol)

        if canonicalize:
            return output_word + self._canonicalize_rotations(output_rotations)
        return output_word + output_rotations
