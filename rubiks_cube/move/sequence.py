from __future__ import annotations

import itertools
import re
from collections.abc import Callable
from collections.abc import Iterator
from collections.abc import Sequence
from typing import Any
from typing import cast
from typing import overload

from rubiks_cube.configuration import CUBE_SIZE
from rubiks_cube.configuration import METRIC
from rubiks_cube.configuration.enumeration import Metric
from rubiks_cube.move import decorate_move
from rubiks_cube.move import format_string_to_moves
from rubiks_cube.move import undecorate_move
from rubiks_cube.move.utils import combine_rotations
from rubiks_cube.move.utils import get_axis
from rubiks_cube.move.utils import invert_move
from rubiks_cube.move.utils import is_niss
from rubiks_cube.move.utils import is_rotation
from rubiks_cube.move.utils import niss_move
from rubiks_cube.move.utils import rotate_move
from rubiks_cube.move.utils import simplyfy_axis_moves
from rubiks_cube.utils.metrics import measure_moves


class MoveSequence(Sequence[str]):
    moves: list[str]

    def __init__(self, moves: str | Sequence[str] | None = None) -> None:
        """Initialize the move sequence.

        Args:
            moves (str | Sequence[str] | None, optional):
                str: String with format "move1 move2 ..."
                Sequence[str]: Sequence of moves. Note: They are not checked for validity.
                None: Empty move sequence.
        """
        if moves is None:
            self.moves = []
        elif isinstance(moves, str):
            self.moves = format_string_to_moves(moves)
        elif isinstance(moves, Sequence):
            self.moves = list(moves)
        else:
            raise ValueError(f"MoveSequence recieved invalid type for moves: {type(moves)}")

    def __str__(self) -> str:
        if len(self.moves) == 0:
            return "None"
        return " ".join(self.moves).replace(") (", " ")

    def __repr__(self) -> str:
        return f'MoveSequence("{str(self)}")'

    def __hash__(self) -> int:
        return hash(str(self))

    def __len__(self) -> int:
        return len(self.moves)

    def __add__(self, other: MoveSequence | Sequence[str]) -> MoveSequence:
        if isinstance(other, MoveSequence):
            return MoveSequence(self.moves + other.moves)
        elif isinstance(other, Sequence):
            return MoveSequence(self.moves + list(other))

    def __radd__(self, other: MoveSequence | Sequence[str]) -> MoveSequence:
        if isinstance(other, MoveSequence):
            return MoveSequence(other.moves + self.moves)
        elif isinstance(other, Sequence):
            return MoveSequence(list(other) + self.moves)

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
        if isinstance(index, slice):
            return self.moves[index]
        elif isinstance(index, int):
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
            fn (Callable[[str], str]): Function to apply to each move string.
        """

        def decorated_fn(move: str) -> Sequence[str]:
            undec_move, niss, slash = undecorate_move(move)
            new_moves = fn(undec_move)
            if isinstance(new_moves, str):
                return [decorate_move(new_moves, niss=niss, slash=slash)]
            return [decorate_move(fn_move, niss=niss, slash=slash) for fn_move in new_moves]

        self.moves = list(itertools.chain(*[decorated_fn(move) for move in self.moves]))


def measure(sequence: MoveSequence, metric: Metric = METRIC) -> int:
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
        "E": ("U", "D'", "y'"),
        "M": ("L'", "R", "x'"),
        "S": ("F'", "B", "z"),
    }

    slice_pattern = re.compile(r"^([EMS])([2']?)$")

    def replace_match(match: re.Match[Any]) -> str:
        slice = match.group(1)
        turn_mod = match.group(2)
        first, second, rot = slice_mapping[slice]

        combined = f"{first}{turn_mod} {second}{turn_mod} {rot}{turn_mod}"
        return combined.replace("''", "").replace("'2", "2")

    sequence.apply(fn=lambda move: slice_pattern.sub(replace_match, move).split())


def replace_wide_moves(sequence: MoveSequence, cube_size: int = CUBE_SIZE) -> None:
    """Inplace replace wide notation wider than cube_size/2.

    Args:
        sequence (MoveSequence): Move sequence.
        cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.
    """

    wide_mapping = {
        "R": ("L", "x", ""),
        "L": ("R", "x", "'"),
        "U": ("D", "y", ""),
        "D": ("U", "y", "'"),
        "F": ("B", "z", ""),
        "B": ("F", "z", "'"),
    }

    wide_pattern = re.compile(r"^([3456789]?)([LRFBUD])w([2']?)$")

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

    sequence.apply(fn=lambda move: wide_pattern.sub(replace_match, move).split())


def shift_rotations_to_end(sequence: MoveSequence) -> MoveSequence:
    """Shift all rotations to the end of the move sequence.

    Args:
        sequence (MoveSequence): Move sequence.

    Returns:
        MoveSequence: Move sequence with rotations at the end.
    """

    rotation_list = []
    output_list = []

    for move in sequence:
        if is_rotation(move):
            rotation_list.append(move)
        else:
            for rotation in reversed(rotation_list):
                move = rotate_move(move, rotation)
            output_list.append(move)

    standard_rotation = combine_rotations(rotation_list)

    return MoveSequence(output_list) + standard_rotation


def combine_axis_moves(sequence: MoveSequence) -> MoveSequence:
    """Combine adjacent moves if they cancel each other, sorted lexically.

    Args:
        sequence (MoveSequence): Move sequence.

    Returns:
        MoveSequence: Combined move sequence.
    """

    output_moves = []

    last_axis = None
    accumulated_moves: list[str] = []
    for move in sequence:
        if is_rotation(move):
            if accumulated_moves:
                output_moves.extend(simplyfy_axis_moves(accumulated_moves))
                accumulated_moves = []
            output_moves.append(move)
            last_axis = None
            continue
        axis = get_axis(move)
        if axis is not None and axis == last_axis:
            accumulated_moves.append(move)
        else:
            output_moves.extend(simplyfy_axis_moves(accumulated_moves))
            accumulated_moves = [move]
            last_axis = axis

    if accumulated_moves:
        output_moves.extend(simplyfy_axis_moves(accumulated_moves))

    output_sequence = MoveSequence(output_moves)

    if output_sequence == sequence:
        return output_sequence
    return combine_axis_moves(output_sequence)


def decompose(sequence: MoveSequence) -> tuple[MoveSequence, MoveSequence]:
    """Decompose a move sequence into inverse and normal moves.

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


def cleanup(sequence: MoveSequence, cube_size: int = CUBE_SIZE) -> MoveSequence:
    """Cleanup a sequence of moves by following these rules:
    - Present normal moves before inverse moves
    - Replace slice notation with normal moves
    - Replace wide notation with normal moves
    - Move all rotations to the end of the sequence.
    - Combine the rotations such that you orient the up face and front face
    - Combine adjacent moves if they cancel each other, sorted lexically

    Args:
        sequence (MoveSequence): Move sequence.
        cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.

    Returns:
        MoveSequence: Cleaned move sequence.
    """
    normal_seq, inverse_seq = decompose(sequence)

    replace_wide_moves(normal_seq, cube_size=cube_size)
    replace_slice_moves(normal_seq)
    normal_seq = shift_rotations_to_end(normal_seq)
    normal_seq = combine_axis_moves(normal_seq)

    replace_wide_moves(inverse_seq, cube_size=cube_size)
    replace_slice_moves(inverse_seq)
    inverse_seq = shift_rotations_to_end(inverse_seq)
    inverse_seq = combine_axis_moves(inverse_seq)
    niss(inverse_seq)

    return normal_seq + inverse_seq
