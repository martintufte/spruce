from __future__ import annotations

import re
from collections.abc import Callable
from collections.abc import Iterator
from collections.abc import Sequence
from typing import TYPE_CHECKING
from typing import Any
from typing import cast
from typing import overload

from attrs import define
from attrs import field
from attrs import validators

from rubiks_cube.configuration import CUBE_SIZE
from rubiks_cube.configuration import DEFAULT_METRIC
from rubiks_cube.configuration.regex import MOVE_REGEX
from rubiks_cube.configuration.regex import SLICE_PATTERN
from rubiks_cube.configuration.regex import WIDE_PATTERN
from rubiks_cube.move.formatting import format_string
from rubiks_cube.move.metrics import measure_moves
from rubiks_cube.move.utils import combine_rotations
from rubiks_cube.move.utils import invert_move
from rubiks_cube.move.utils import is_rotation
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
            n_normal = len(self.normal)
            if index < 0:
                index += len(self)
            if index < 0 or index >= len(self):
                raise IndexError("Invalid index provided for MoveSequence.")
            if index < n_normal:
                return self.normal[index]
            return unstrip_move(self.inverse[index - n_normal])

        if isinstance(index, slice):
            return self.moves[index]

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

    def __invert__(self) -> MoveSequence:
        return MoveSequence(
            normal=[invert_move(move) for move in reversed(self.normal)],
            inverse=[invert_move(move) for move in reversed(self.inverse)],
        )

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
        metric (str, optional): Metric to use. Defaults to METRIC.

    Returns:
        int: Length of the move sequence.
    """
    return measure_moves(sequence.normal, metric=metric) + measure_moves(
        sequence.inverse, metric=metric
    )


def replace_slice_moves(sequence: MoveSequence) -> None:
    """Inplace replace slice notation.

    Args:
        sequence (MoveSequence): Move sequence.
    """
    slice_mapping = {
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

    sequence.apply(fn=lambda move: SLICE_PATTERN.sub(replace_match, move).split())


def replace_wide_moves(sequence: MoveSequence, cube_size: int = CUBE_SIZE) -> None:
    """Inplace replace wide notation wider than cube_size/2.

    Args:
        sequence (MoveSequence): Move sequence.
        cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.
    """
    wide_mapping = {
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

    sequence.apply(fn=lambda move: WIDE_PATTERN.sub(replace_match, move).split())


def _shift_rotations_to_end_side(moves: list[str]) -> list[str]:
    rotation_list: list[str] = []
    output_list: list[str] = []

    for move in moves:
        if is_rotation(move):
            rotation_list.append(move)
        else:
            rotated_move = move
            for rotation in reversed(rotation_list):
                rotated_move = rotate_move(rotated_move, rotation)
            output_list.append(rotated_move)

    return output_list + combine_rotations(rotation_list)


def shift_rotations_to_end(sequence: MoveSequence) -> None:
    """Shift all rotations to the end of the move sequence.

    Args:
        sequence (MoveSequence): Move sequence.
    """
    sequence.normal = _shift_rotations_to_end_side(sequence.normal)
    sequence.inverse = _shift_rotations_to_end_side(sequence.inverse)


def _try_cancel_side(moves: list[str], move_meta: MoveMeta) -> list[str]:
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
        if is_rotation(move):
            if segment:
                output.extend(reduce_segment(segment))
                segment = []
            output.append(move)
            continue
        segment.append(move)

    if segment:
        output.extend(reduce_segment(segment))

    return output


def try_cancel_moves(sequence: MoveSequence, move_meta: MoveMeta) -> None:
    """Try to cancel and combine non-rotations using permutation closure and commutation."""
    sequence.normal = _try_cancel_side(sequence.normal, move_meta)
    sequence.inverse = _try_cancel_side(sequence.inverse, move_meta)


def decompose(sequence: MoveSequence) -> tuple[MoveSequence, MoveSequence]:
    """Decompose a move sequence into normal and inverse moves.

    Args:
        sequence (MoveSequence): Move sequence.

    Returns:
        tuple[MoveSequence, MoveSequence]: Normal and inverse move sequences.
    """
    return (
        MoveSequence(normal=sequence.normal),
        MoveSequence(normal=sequence.inverse),
    )


def niss(sequence: MoveSequence) -> None:
    """Inplace niss a move sequence.

    Args:
        sequence (MoveSequence): Move sequence.
    """
    sequence.normal, sequence.inverse = sequence.inverse, sequence.normal


def unniss(sequence: MoveSequence) -> MoveSequence:
    """Unniss a move sequence.

    Args:
        sequence (MoveSequence): Move sequence.

    Returns:
        MoveSequence: Unnissed move sequence.
    """
    return MoveSequence(
        normal=[
            *sequence.normal,
            *(invert_move(move) for move in reversed(sequence.inverse)),
        ]
    )


def cleanup(sequence: MoveSequence, move_meta: MoveMeta) -> MoveSequence:
    """Cleanup a sequence of moves.

    Steps:
        - Present normal moves before inverse moves
        - Replace slice notation with normal moves
        - Replace wide notation with normal moves
        - Move all rotations to the end of the sequence.
        - Combine the rotations such that you orient the up face and front face
        - Cancel and combine moves using permutation closure and commutation

    Args:
        sequence (MoveSequence): Move sequence.
        move_meta (MoveMeta): Move meta configuration.

    Returns:
        MoveSequence: Cleaned move sequence.
    """
    normal_seq, inverse_seq = decompose(sequence)

    replace_wide_moves(normal_seq, cube_size=move_meta.cube_size)
    replace_slice_moves(normal_seq)
    shift_rotations_to_end(normal_seq)
    try_cancel_moves(normal_seq, move_meta)

    replace_wide_moves(inverse_seq, cube_size=move_meta.cube_size)
    replace_slice_moves(inverse_seq)
    shift_rotations_to_end(inverse_seq)
    try_cancel_moves(inverse_seq, move_meta)
    niss(inverse_seq)

    return normal_seq + inverse_seq
