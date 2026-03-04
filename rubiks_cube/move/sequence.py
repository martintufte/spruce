from __future__ import annotations

import re
from collections.abc import Callable
from collections.abc import Iterator
from collections.abc import Sequence
from typing import TYPE_CHECKING
from typing import Any
from typing import Final
from typing import cast
from typing import overload

from attrs import define
from attrs import field
from attrs import validators

from rubiks_cube.configuration import DEFAULT_METRIC
from rubiks_cube.configuration.regex import MOVE_REGEX
from rubiks_cube.configuration.regex import SLICE_PATTERN
from rubiks_cube.configuration.regex import WIDE_PATTERN
from rubiks_cube.move.formatting import format_string
from rubiks_cube.move.metrics import measure_moves
from rubiks_cube.move.utils import rotate_move
from rubiks_cube.move.utils import strip_move
from rubiks_cube.move.utils import unstrip_move

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

        return MoveSequence(normal=normal, inverse=inverse)

    def __str__(self) -> str:
        if len(self) == 0:
            return "None"
        components: list[str] = []
        if self.normal:
            components.append(" ".join(self.normal))
        if self.inverse:
            components.append("(" + " ".join(self.inverse) + ")")
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
                    raise IndexError("Invalid index provided for MoveSequence.")
                return self.normal[index]

            inverse_index = abs(index) - 1
            if inverse_index >= len(self.inverse):
                raise IndexError("Invalid index provided for MoveSequence.")
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

        raise IndexError("Invalid index provided for MoveSequence.")

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


def measure(sequence: MoveSequence, metric: Metric = DEFAULT_METRIC) -> int:
    """Measure the length of a move sequence using the metric.

    Args:
        sequence (MoveSequence): Move sequence.
        metric (str, optional): Metric to use. Defaults to DEFAULT_METRIC.

    Returns:
        int: Length of the move sequence.
    """
    return measure_moves(sequence.normal, metric=metric) + measure_moves(
        sequence.inverse, metric=metric
    )


# TODO: Consider not hardcoding
SLICE_MAPPING: Final[dict[str, tuple[str, str, str]]] = {
    "M": ("L'", "R", "x'"),
    "E": ("U", "D'", "y'"),
    "S": ("F'", "B", "z"),
}


# TODO: Consider not hardcoding
WIDE_MAPPING: Final[dict[str, tuple[str, str, str]]] = {
    "L": ("R", "x", "'"),
    "R": ("L", "x", ""),
    "F": ("B", "z", ""),
    "B": ("F", "z", "'"),
    "U": ("D", "y", ""),
    "D": ("U", "y", "'"),
}


def replace_slice_moves(sequence: MoveSequence, move_meta: MoveMeta) -> None:
    """Inplace replace slice notation.

    Args:
        sequence (MoveSequence): Move sequence.
    """

    def replace_match(match: re.Match[Any]) -> str:
        slice = match.group(1)
        turn_mod = match.group(2)
        first, second, rot = SLICE_MAPPING[slice]

        combined = f"{first}{turn_mod} {second}{turn_mod} {rot}{turn_mod}"
        return combined.replace("''", "").replace("'2", "2")

    sequence.apply(fn=lambda move: SLICE_PATTERN.sub(replace_match, move).split())


def replace_wide_moves(sequence: MoveSequence, move_meta: MoveMeta) -> None:
    """Inplace replace wide notation wider than cube_size/2.

    Args:
        sequence (MoveSequence): Move sequence.
        cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.
    """

    def replace_match(match: re.Match[Any]) -> str:
        wide = match.group(1) or "2"
        diff = move_meta.cube_size - int(wide)
        if diff >= move_meta.cube_size / 2:
            return cast("str", match.string)

        wide_mod = "w" if diff > 1 else ""
        diff_mod = str(diff) if diff > 2 else ""
        turn_mod = match.group(3)
        move = match.group(2)
        base, rot, rot_mod = WIDE_MAPPING[move]
        rot_mod = f"{rot_mod}{turn_mod}".replace("''", "").replace("'2", "2")

        if diff < 1:
            return f"{rot}{rot_mod}"
        return f"{diff_mod}{base}{wide_mod}{turn_mod} {rot}{rot_mod}"

    sequence.apply(fn=lambda move: WIDE_PATTERN.sub(replace_match, move).split())


def _shift_rotations_to_end_side(moves: list[str], move_meta: MoveMeta) -> list[str]:
    output_rotations: list[str] = []
    output_moves: list[str] = []

    for move in moves:
        if move_meta.is_rotation(move):
            output_rotations.append(move)
        else:
            rotated_move = move
            for rotation in reversed(output_rotations):
                rotated_move = rotate_move(rotated_move, rotation)
            output_moves.append(rotated_move)

    if move_meta is not None:
        return output_moves + move_meta.get_canonical_rotation(output_rotations)
    return output_moves + output_rotations


def shift_rotations_to_end(sequence: MoveSequence, move_meta: MoveMeta) -> None:
    """Shift all rotations to the end of the move sequence.

    Args:
        sequence (MoveSequence): Move sequence.
        move_meta (MoveMeta): Move meta configuration.
    """
    sequence.normal = _shift_rotations_to_end_side(sequence.normal, move_meta)
    sequence.inverse = _shift_rotations_to_end_side(sequence.inverse, move_meta)


def _cancel_side(moves: list[str], move_meta: MoveMeta) -> list[str]:
    def is_legal(move: str) -> bool:
        return move in move_meta.legal_moves

    def can_commute_over(move: str, between: list[str]) -> bool:
        return all(between_move in move_meta.commutes[move] for between_move in between)

    def reduce_segment(moves: list[str]) -> list[str]:
        """Reduce a rotation-free segment by commuting and combining closed moves."""
        stack: list[str] = []
        for move in moves:
            stack.append(move)
            if not is_legal(move):
                continue
            while stack:
                current = stack[-1]
                if not is_legal(current):
                    break
                combined_pos: int | None = None
                combined_move: str | None = None
                for pos in range(len(stack) - 2, -1, -1):
                    previous = stack[pos]
                    if not is_legal(previous):
                        break
                    if not can_commute_over(previous, stack[pos + 1 : -1]):
                        continue
                    combined = move_meta.compose.get((previous, current))
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
    for move in moves:
        if move_meta.is_rotation(move):
            if segment:
                output.extend(reduce_segment(segment))
                segment = []
            output.append(move)
            continue
        segment.append(move)

    if segment:
        output.extend(reduce_segment(segment))

    return output


def cancel_moves(sequence: MoveSequence, move_meta: MoveMeta) -> None:
    """Try to cancel and combine non-rotations using permutation composition and commutativity."""
    sequence.normal = _cancel_side(sequence.normal, move_meta)
    sequence.inverse = _cancel_side(sequence.inverse, move_meta)


def unniss(sequence: MoveSequence, move_meta: MoveMeta) -> MoveSequence:
    """Unniss a move sequence.

    Args:
        sequence (MoveSequence): Move sequence.

    Returns:
        MoveSequence: Unnissed move sequence.
    """
    return MoveSequence(normal=[*sequence.normal, *move_meta.invert(sequence.inverse)])


def invert(sequence: MoveSequence, move_meta: MoveMeta) -> MoveSequence:
    """Try to invert the move sequence."""
    return MoveSequence(
        normal=move_meta.invert(sequence.normal),
        inverse=move_meta.invert(sequence.inverse),
    )


def cleanup(sequence: MoveSequence, move_meta: MoveMeta) -> MoveSequence:
    """Cleanup a sequence of moves.

    Args:
        sequence (MoveSequence): Move sequence.
        move_meta (MoveMeta): Move meta configuration.

    Returns:
        MoveSequence: Cleaned sequence of moves.
    """
    replace_wide_moves(sequence, move_meta)
    replace_slice_moves(sequence, move_meta)
    shift_rotations_to_end(sequence, move_meta)
    cancel_moves(sequence, move_meta)

    return sequence
