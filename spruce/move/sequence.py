from __future__ import annotations

import re
from typing import TYPE_CHECKING
from typing import Any

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
    from collections.abc import Iterable
    from collections.abc import Sequence

    from spruce.configuration.enumeration import Metric
    from spruce.move.meta import MoveMeta


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

            stripped_move = MoveSymbol(strip_move(move))

            if not re.match(MOVE_REGEX, stripped_move):
                raise ValueError(f"Could not format string to moves. Got: {stripped_move}")

            if niss:
                inverse.append(stripped_move)
            else:
                normal.append(stripped_move)

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

    def __eq__(self, other: Any) -> bool:
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

    def apply(self, /, fn: Callable[[MoveSymbol], MoveSymbol | Sequence[MoveSymbol]]) -> None:
        """Apply a function to each move in the sequence.

        Args:
            fn (Callable[[MoveSymbol], MoveSymbol | Sequence[MoveSymbol]]): Function to apply to
                each move symbol.
        """

        def apply_to_iterable(word: Iterable[MoveSymbol]) -> list[MoveSymbol]:
            out: list[MoveSymbol] = []
            for symbol in word:
                new_symbols = fn(symbol)
                if isinstance(new_symbols, str):
                    out.append(MoveSymbol(new_symbols))
                else:
                    out.extend(new_symbols)
            return out

        self.normal = apply_to_iterable(self.normal)
        self.inverse = apply_to_iterable(self.inverse)


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
