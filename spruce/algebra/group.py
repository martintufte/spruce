"""A labelled permutation group: symbols, their permutations, and the tables they induce."""

from __future__ import annotations

from enum import Enum
from enum import unique
from functools import cached_property
from typing import TYPE_CHECKING

import attrs
import numpy as np

from spruce.algebra.permutation import invert
from spruce.types import MoveSymbol

if TYPE_CHECKING:
    from collections.abc import Callable
    from collections.abc import Iterable
    from collections.abc import Sequence
    from collections.abc import Set as AbstractSet

    from spruce.types import PermutationArray


type SortKey = Callable[[MoveSymbol], tuple[int, ...]]
type RotationCanonicalizer = Callable[[Sequence[MoveSymbol], "MoveMeta"], list[MoveSymbol]]


def default_sort_key(symbol: MoveSymbol) -> tuple[int, ...]:
    """Rank a symbol by its characters, for groups with no notation of their own."""
    return tuple(ord(char) for char in symbol)


@unique
class PermutationClassification(Enum):
    """The role a symbol's permutation plays in the group it labels."""

    ALGORITHM = "ALGORITHM"
    BASE = "BASE"
    IDENTITY = "IDENTITY"
    ROTATION = "ROTATION"


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

    # Identity, only used in messages
    name: str

    # Supplied by the puzzle that builds the group
    default_generator_symbols: frozenset[MoveSymbol] | None = None
    rotation_canonicalizer: RotationCanonicalizer | None = None

    @cached_property
    def symbols(self) -> frozenset[MoveSymbol]:
        return frozenset(self.permutations)

    def _reject_unknown(self, symbols: Iterable[str]) -> None:
        """Raise if any string is not a move symbol of this group."""
        unknown = sorted(symbol for symbol in symbols if symbol not in self.symbols)
        if unknown:
            raise ValueError(f"Unknown move symbols {unknown} for {self.name}")

    def to_symbols(self, *symbols: str) -> frozenset[MoveSymbol]:
        """Validate plain strings as a set of move symbols of this group.

        Together with `to_word` and `to_sequence` this is the only supported way to turn
        strings into `MoveSymbol`s, so that no unvalidated symbol can enter the system.

        Raises:
            ValueError: If any string is not a move symbol of this group.
        """
        self._reject_unknown(symbols)

        return frozenset(MoveSymbol(symbol) for symbol in symbols)

    def to_word(self, symbols: Iterable[str]) -> list[MoveSymbol]:
        """Validate plain strings as an ordered word of this group.

        Raises:
            ValueError: If any string is not a move symbol of this group.
        """
        word = list(symbols)
        self._reject_unknown(word)

        return [MoveSymbol(symbol) for symbol in word]

    @property
    def default_generator(self) -> frozenset[MoveSymbol]:
        """The generator used when the caller has no preference for this group.

        Raises:
            ValueError: If the group was built without a default generator.
        """
        if self.default_generator_symbols is None:
            raise ValueError(f"No default generator defined for {self.name}")
        return self.default_generator_symbols

    def get_actions(
        self,
        generator: AbstractSet[MoveSymbol],
        expand: bool = True,
    ) -> dict[MoveSymbol, PermutationArray]:
        """Build the action map for a set of move symbols using this puzzle's move metadata.

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
    def from_permutations(
        cls,
        permutations: dict[MoveSymbol, PermutationArray],
        classifications: dict[MoveSymbol, PermutationClassification],
        name: str,
        substitutions: dict[MoveSymbol, tuple[MoveSymbol, ...]] | None = None,
        sort_key: SortKey | None = None,
        default_generator_symbols: frozenset[MoveSymbol] | None = None,
        rotation_canonicalizer: RotationCanonicalizer | None = None,
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
        if sort_key is None:
            sort_key = default_sort_key

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
            name=name,
            default_generator_symbols=default_generator_symbols,
            rotation_canonicalizer=rotation_canonicalizer,
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
            if self.rotation_canonicalizer is None:
                raise ValueError(f"No rotation canonicalizer defined for {self.name}")
            return output_word + self.rotation_canonicalizer(output_rotations, self)
        return output_word + output_rotations
