from __future__ import annotations

import re
from collections.abc import Callable
from collections.abc import Iterator
from collections.abc import Sequence
from typing import TYPE_CHECKING
from typing import Any
from typing import overload

from attrs import define
from attrs import field
from attrs import validators

from rubiks_cube.configuration.regex import MOVE_REGEX
from rubiks_cube.move.formatting import format_string
from rubiks_cube.move.formatting import strip_move
from rubiks_cube.move.formatting import unstrip_move
from rubiks_cube.move.metrics import measure_moves

if TYPE_CHECKING:
    from rubiks_cube.configuration.enumeration import Metric
    from rubiks_cube.move.meta import MoveMeta


@define(eq=False, repr=False)
class MoveSequence(Sequence[str]):
    normal: list[str] = field(
        factory=list,
        validator=validators.deep_iterable(
            member_validator=validators.instance_of(str),
            iterable_validator=validators.instance_of(list),
        ),
    )
    inverse: list[str] = field(
        factory=list,
        validator=validators.deep_iterable(
            member_validator=validators.instance_of(str),
            iterable_validator=validators.instance_of(list),
        ),
    )

    @property
    def moves(self) -> list[str]:
        return [*self.normal, *(unstrip_move(move) for move in self.inverse)]

    @classmethod
    def from_str(cls, string: str) -> MoveSequence:
        formatted_string = format_string(string)

        normal = []
        inverse = []
        niss = False
        for move in formatted_string.split():
            if move.startswith("("):
                niss = not niss

            stripped_move = strip_move(move)

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

    def __radd__(self, other: MoveSequence | Sequence[str]) -> MoveSequence:
        if isinstance(other, MoveSequence):
            return MoveSequence(
                normal=[*other.normal, *self.normal],
                inverse=[*other.inverse, *self.inverse],
            )
        if isinstance(other, Sequence):
            return other + self
        return NotImplemented

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, MoveSequence):
            return self.normal == other.normal and self.inverse == other.inverse
        return False

    def __ne__(self, other: Any) -> bool:
        if isinstance(other, MoveSequence):
            return self.normal != other.normal or self.inverse != other.inverse
        return True

    @overload
    def __getitem__(self, index: int) -> str: ...

    @overload
    def __getitem__(self, index: slice) -> Sequence[str]: ...

    def __getitem__(self, index: int | slice) -> str | Sequence[str]:
        if isinstance(index, int):
            if index >= 0:
                if index >= len(self.normal):
                    raise IndexError(f"Invalid index provided for {self.__class__.__name__}.")
                return self.normal[index]

            inverse_index = abs(index) - 1
            if inverse_index >= len(self.inverse):
                raise IndexError(f"Invalid index provided for {self.__class__.__name__}.")
            return unstrip_move(self.inverse[inverse_index])

        if isinstance(index, slice):
            start, stop, step = index.start, index.stop, index.step

            # Keep slices on one side only: non-negative indexes for normal,
            # negative indexes for inverse.
            if start is not None and stop is not None and ((start >= 0) != (stop >= 0)):
                raise IndexError("Slice crosses normal/inverse boundary.")

            inverse_moves = [unstrip_move(move) for move in self.inverse]

            def as_inverse_index(value: int | None) -> int | None:
                if value is None:
                    return None
                if value >= 0:
                    raise IndexError("Slice crosses normal/inverse boundary.")
                return abs(value) - 1

            if start is None and stop is None:
                if self.normal and self.inverse:
                    raise IndexError("Slice crosses normal/inverse boundary.")
                if self.normal:
                    return self.normal[slice(None, None, step)]
                return inverse_moves[slice(None, None, step)]

            if (start is not None and start < 0) or (stop is not None and stop < 0):
                return inverse_moves[slice(as_inverse_index(start), as_inverse_index(stop), step)]

            return self.normal[slice(start, stop, step)]

        raise IndexError(f"Invalid index provided for {self.__class__.__name__}.")

    def __iter__(self) -> Iterator[str]:
        yield from self.normal
        for move in self.inverse:
            yield unstrip_move(move)

    def __contains__(self, item: object) -> bool:
        return item in self.moves

    def __bool__(self) -> bool:
        return bool(self.normal or self.inverse)

    def __copy__(self) -> MoveSequence:
        return MoveSequence(normal=self.normal.copy(), inverse=self.inverse.copy())

    def __lt__(self, other: MoveSequence | Sequence[str]) -> bool:
        return len(self) < len(other)

    def __le__(self, other: MoveSequence | Sequence[str]) -> bool:
        return len(self) <= len(other)

    def __gt__(self, other: MoveSequence | Sequence[str]) -> bool:
        return len(self) > len(other)

    def __ge__(self, other: MoveSequence | Sequence[str]) -> bool:
        return len(self) >= len(other)

    def __mul__(self, other: int) -> MoveSequence:
        return MoveSequence(
            normal=self.normal * other,
            inverse=self.inverse * other,
        )

    def __rmul__(self, other: int) -> MoveSequence:
        return self * other

    def __reversed__(self) -> Iterator[str]:
        return reversed(self.moves)

    def apply(self, /, fn: Callable[[str], str | Sequence[str]]) -> None:
        """Apply a function to each move in the sequence.

        Args:
            fn (Callable[[str], str]): Function to apply to each string of move.
        """

        def apply_to_list(moves: list[str]) -> list[str]:
            out: list[str] = []
            for move in moves:
                new_moves = fn(move)
                if isinstance(new_moves, str):
                    out.append(new_moves)
                else:
                    out.extend(new_moves)
            return out

        self.normal = apply_to_list(self.normal)
        self.inverse = apply_to_list(self.inverse)


def measure(sequence: MoveSequence, metric: Metric) -> int:
    """Measure the length of a move sequence using the metric.

    Args:
        sequence (MoveSequence): Move sequence.
        metric (Metric): Metric.

    Returns:
        int: Length of the move sequence.
    """
    return measure_moves(sequence.normal, metric=metric) + measure_moves(
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
        normal=move_meta.invert(sequence.normal), inverse=move_meta.invert(sequence.inverse)
    )


def cleanup(sequence: MoveSequence, move_meta: MoveMeta) -> MoveSequence:
    """Cleanup a sequence of moves."""
    sequence.apply(move_meta.substitute)
    shift_rotations_to_end(sequence, move_meta, canonicalize=True)
    reduce(sequence, move_meta)

    return sequence
