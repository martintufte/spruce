from __future__ import annotations

import re
from typing import TYPE_CHECKING

from attrs import define
from attrs import field
from attrs import validators

from spruce.configuration.regex import MOVE_REGEX
from spruce.move.formatting import format_string
from spruce.move.formatting import strip_move
from spruce.move.metrics import measure_word
from spruce.types import MoveSymbol

if TYPE_CHECKING:
    from collections.abc import Callable
    from collections.abc import Sequence

    from spruce.algebra.meta import MoveMeta
    from spruce.puzzle.cube.metrics import Metric


@define(eq=False, repr=False)
class MoveSequence:
    """A sequence of moves, split into a normal and an inverse (NISS) side."""

    normal: list[MoveSymbol] = field(
        factory=list,
        validator=validators.deep_iterable(
            member_validator=validators.instance_of(str),
            iterable_validator=validators.instance_of(list),
        ),
    )
    inverse: list[MoveSymbol] = field(
        factory=list,
        validator=validators.deep_iterable(
            member_validator=validators.instance_of(str),
            iterable_validator=validators.instance_of(list),
        ),
    )

    @classmethod
    def from_str(cls, string: str) -> MoveSequence:
        formatted_string = format_string(string)

        normal: list[MoveSymbol] = []
        inverse: list[MoveSymbol] = []
        niss = False
        for move in formatted_string.split():
            if move.startswith("("):
                niss = not niss

            symbol = MoveSymbol(strip_move(move))

            if not re.match(MOVE_REGEX, symbol):
                raise ValueError(f"Could not format string to moves. Got: {symbol}")

            if niss:
                inverse.append(symbol)
            else:
                normal.append(symbol)

            if move.endswith(")"):
                niss = not niss

        return cls(normal=normal, inverse=inverse)

    def __str__(self) -> str:
        if len(self) == 0:
            return "None"
        components: list[str] = []
        if self.normal:
            components.append(" ".join(self.normal))
        if self.inverse:
            components.append(f"({' '.join(self.inverse)})")
        return " ".join(components)

    def __repr__(self) -> str:
        if len(self) == 0:
            return f"{self.__class__.__name__}()"
        return f'{self.__class__.__name__}.from_str("{self!s}")'

    def __hash__(self) -> int:
        return hash(str(self))

    def __len__(self) -> int:
        return len(self.normal) + len(self.inverse)

    def __add__(self, other: MoveSequence) -> MoveSequence:
        if isinstance(other, MoveSequence):
            return MoveSequence(
                normal=[*self.normal, *other.normal],
                inverse=[*self.inverse, *other.inverse],
            )
        return NotImplemented

    def __eq__(self, other: object) -> bool:
        if isinstance(other, MoveSequence):
            return self.normal == other.normal and self.inverse == other.inverse
        return False

    def __bool__(self) -> bool:
        return bool(self.normal or self.inverse)

    def __copy__(self) -> MoveSequence:
        return MoveSequence(normal=self.normal.copy(), inverse=self.inverse.copy())

    def __lt__(self, other: MoveSequence) -> bool:
        return len(self) < len(other)

    def __le__(self, other: MoveSequence) -> bool:
        return len(self) <= len(other)

    def __gt__(self, other: MoveSequence) -> bool:
        return len(self) > len(other)

    def __ge__(self, other: MoveSequence) -> bool:
        return len(self) >= len(other)

    def __mul__(self, other: int) -> MoveSequence:
        return MoveSequence(
            normal=self.normal * other,
            inverse=self.inverse * other,
        )

    def __rmul__(self, other: int) -> MoveSequence:
        return self * other

    def apply(self, /, fn: Callable[[MoveSymbol], Sequence[MoveSymbol]]) -> None:
        """Apply a function to each move in the sequence, flattening the resulting words.

        Args:
            fn (Callable[[MoveSymbol], Sequence[MoveSymbol]]): Function mapping each move
                symbol to the word it expands to.
        """
        self.normal = [new_symbol for symbol in self.normal for new_symbol in fn(symbol)]
        self.inverse = [new_symbol for symbol in self.inverse for new_symbol in fn(symbol)]


def sequence_from_word(word: Sequence[MoveSymbol], on_inverse: bool = False) -> MoveSequence:
    """Build a sequence from a word, placing it on the normal or the inverse side."""
    if on_inverse:
        return MoveSequence(inverse=list(word))
    return MoveSequence(normal=list(word))


def measure(sequence: MoveSequence, metric: Metric) -> int:
    """Measure the length of a move sequence using the metric."""
    return measure_word(sequence.normal, metric=metric) + measure_word(
        sequence.inverse, metric=metric
    )


def shift_rotations_to_end(sequence: MoveSequence, move_meta: MoveMeta, canonicalize: bool) -> None:
    """Shift all rotations to the end of the move sequence."""
    sequence.normal = move_meta.shift_rotations_to_end(sequence.normal, canonicalize=canonicalize)
    sequence.inverse = move_meta.shift_rotations_to_end(sequence.inverse, canonicalize=canonicalize)


def reduce(sequence: MoveSequence, move_meta: MoveMeta) -> None:
    """Try to reduce the normal and inverse sequence of moves."""
    sequence.normal = move_meta.reduce(sequence.normal)
    sequence.inverse = move_meta.reduce(sequence.inverse)


def unniss(sequence: MoveSequence, move_meta: MoveMeta) -> MoveSequence:
    """Unniss a move sequence by converting all inverse moves to normal moves."""
    return MoveSequence(normal=[*sequence.normal, *move_meta.invert(sequence.inverse)])


def invert(sequence: MoveSequence, move_meta: MoveMeta) -> MoveSequence:
    """Try to invert the move sequence."""
    return MoveSequence(
        normal=move_meta.invert(sequence.normal),
        inverse=move_meta.invert(sequence.inverse),
    )


def cleanup(sequence: MoveSequence, move_meta: MoveMeta) -> MoveSequence:
    """Cleanup a sequence of moves."""
    sequence.apply(move_meta.substitute)
    shift_rotations_to_end(sequence, move_meta, canonicalize=True)
    reduce(sequence, move_meta)

    return sequence
