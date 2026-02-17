from __future__ import annotations

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
from rubiks_cube.formatting import format_string_to_moves
from rubiks_cube.formatting.decorator import decorate_move
from rubiks_cube.formatting.decorator import undecorate_move
from rubiks_cube.formatting.regex import SLICE_PATTERN
from rubiks_cube.formatting.regex import WIDE_PATTERN
from rubiks_cube.move.metrics import measure_moves
from rubiks_cube.move.utils import combine_rotations
from rubiks_cube.move.utils import invert_move
from rubiks_cube.move.utils import is_niss
from rubiks_cube.move.utils import is_rotation
from rubiks_cube.move.utils import niss_move
from rubiks_cube.move.utils import rotate_move

if TYPE_CHECKING:
    import re

    from rubiks_cube.configuration.enumeration import Metric
    from rubiks_cube.move.meta import MoveMeta


@define(eq=False, repr=False)
class MoveSequence(Sequence[str]):
    moves: list[str] = field(
        factory=list,
        validator=validators.deep_iterable(
            member_validator=validators.instance_of(str),
            iterable_validator=validators.instance_of(list),
        ),
    )

    @classmethod
    def from_str(cls, moves: str) -> MoveSequence:
        return cls(format_string_to_moves(moves))

    def __str__(self) -> str:
        if len(self.moves) == 0:
            return "None"
        return " ".join(self.moves).replace(") (", " ").replace("~ ~", " ")

    def __repr__(self) -> str:
        if len(self.moves) == 0:
            return f"{self.__class__.__name__}()"
        return f'{self.__class__.__name__}.from_str("{self!s}")'

    def __hash__(self) -> int:
        return hash(str(self))

    def __len__(self) -> int:
        return len(self.moves)

    def __add__(self, other: MoveSequence | Sequence[str]) -> MoveSequence:
        if isinstance(other, MoveSequence):
            return MoveSequence(self.moves + other.moves)
        if isinstance(other, Sequence):
            return MoveSequence(self.moves + list(other))
        return NotImplemented

    def __radd__(self, other: MoveSequence | Sequence[str]) -> MoveSequence:
        if isinstance(other, MoveSequence):
            return MoveSequence(other.moves + self.moves)
        if isinstance(other, Sequence):
            return MoveSequence(list(other) + self.moves)
        return NotImplemented

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, MoveSequence):
            return self.moves == other.moves
        return False

    def __ne__(self, other: Any) -> bool:
        if isinstance(other, MoveSequence):
            return self.moves != other.moves
        return True

    @overload
    def __getitem__(self, index: int) -> str: ...

    @overload
    def __getitem__(self, index: slice) -> Sequence[str]: ...

    def __getitem__(self, index: int | slice) -> str | Sequence[str]:
        if isinstance(index, (slice, int)):
            return self.moves[index]
        raise IndexError("Invalid index provided for MoveSequence.")

    def __iter__(self) -> Iterator[str]:
        for move in self.moves:
            yield move

    def __contains__(self, item: object) -> bool:
        return item in self.moves

    def __bool__(self) -> bool:
        return bool(self.moves)

    def __copy__(self) -> MoveSequence:
        return MoveSequence(moves=self.moves.copy())

    def __lt__(self, other: MoveSequence | Sequence[str]) -> bool:
        return len(self) < len(other)

    def __le__(self, other: MoveSequence | Sequence[str]) -> bool:
        return len(self) <= len(other)

    def __gt__(self, other: MoveSequence | Sequence[str]) -> bool:
        return len(self) > len(other)

    def __ge__(self, other: MoveSequence | Sequence[str]) -> bool:
        return len(self) >= len(other)

    def __mul__(self, other: int) -> MoveSequence:
        return MoveSequence(self.moves * other)

    def __rmul__(self, other: int) -> MoveSequence:
        return MoveSequence(other * self.moves)

    def __reversed__(self) -> Iterator[str]:
        return reversed(self.moves)

    def __invert__(self) -> MoveSequence:
        inverse_sequence = MoveSequence(moves=list(reversed(self.moves)))
        inverse_sequence.apply(fn=invert_move)
        return inverse_sequence

    def apply(self, /, fn: Callable[[str], str | Sequence[str]]) -> None:
        """Apply a function to each move in the sequence. Keep decorations.

        Args:
            fn (Callable[[str], str]): Function to apply to each string of move.
        """

        def decorated_fn(move: str) -> Sequence[str]:
            undec_move, niss = undecorate_move(move)
            new_moves = fn(undec_move)
            if isinstance(new_moves, str):
                return [decorate_move(new_moves, niss=niss)]
            return [decorate_move(fn_move, niss=niss) for fn_move in new_moves]

        self.moves = [
            decorated_move for move in self.moves for decorated_move in decorated_fn(move)
        ]


def measure(sequence: MoveSequence, metric: Metric = DEFAULT_METRIC) -> int:
    """Measure the length of a move sequence using the metric.

    Args:
        sequence (MoveSequence): Move sequence.
        metric (str, optional): Metric to use. Defaults to METRIC.

    Returns:
        int: Length of the move sequence.
    """
    return measure_moves(sequence.moves, metric=metric)


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


def shift_rotations_to_end(sequence: MoveSequence) -> None:
    """Shift all rotations to the end of the move sequence.

    Args:
        sequence (MoveSequence): Move sequence.
    """
    rotation_list = []
    output_list = []

    for move in sequence:
        if is_rotation(move):
            rotation_list.append(move)
        else:
            rotated_move = move
            for rotation in reversed(rotation_list):
                rotated_move = rotate_move(rotated_move, rotation)
            output_list.append(rotated_move)

    sequence.moves = output_list + combine_rotations(rotation_list)


def try_cancel_moves(sequence: MoveSequence, move_meta: MoveMeta) -> None:
    """Try to cancel and combine non-rotations using permutation closure and commutation."""

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
    for move in sequence:
        if is_rotation(move):
            if segment:
                output.extend(reduce_segment(segment))
                segment = []
            output.append(move)
            continue
        segment.append(move)

    if segment:
        output.extend(reduce_segment(segment))

    sequence.moves = output


def decompose(sequence: MoveSequence) -> tuple[MoveSequence, MoveSequence]:
    """Decompose a move sequence into normal and inverse moves.

    Args:
        sequence (MoveSequence): Move sequence.

    Returns:
        tuple[MoveSequence, MoveSequence]: Normal and inverse move sequences.
    """
    normal_moves: list[str] = []
    inverse_moves: list[str] = []

    for move in sequence:
        if is_niss(move):
            inverse_moves.append(move[1:-1])
        else:
            normal_moves.append(move)

    return MoveSequence(normal_moves), MoveSequence(inverse_moves)


def niss(sequence: MoveSequence) -> None:
    """Inplace niss a move sequence.

    Args:
        sequence (MoveSequence): Move sequence.
    """
    sequence.moves = [niss_move(move) for move in sequence.moves]


def unniss(sequence: MoveSequence) -> MoveSequence:
    """Unniss a move sequence.

    Args:
        sequence (MoveSequence): Move sequence.

    Returns:
        MoveSequence: Unnissed move sequence.
    """
    normal_seq, inverse_seq = decompose(sequence)

    return normal_seq + ~inverse_seq


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
