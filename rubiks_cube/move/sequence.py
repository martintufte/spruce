from __future__ import annotations

import re
import itertools
from typing import Any
from typing import Callable

from rubiks_cube.configuration import CUBE_SIZE
from rubiks_cube.configuration import METRIC
from rubiks_cube.move import get_axis
from rubiks_cube.move import invert_move
from rubiks_cube.move import is_rotation
from rubiks_cube.move import niss_move
from rubiks_cube.move import rotate_move
from rubiks_cube.move import format_string_to_moves
from rubiks_cube.move import strip_move
from rubiks_cube.move.utils import combine_rotations
from rubiks_cube.move.utils import simplyfy_axis_moves
from rubiks_cube.utils.formatter import remove_comment
from rubiks_cube.utils.metrics import count_length


class MoveSequence:
    """Rubiks cube move sequence represented with a list of strings."""

    def __init__(self, moves: str | list[str] | None = None) -> None:
        if moves is None:
            self.moves = []
        elif isinstance(moves, str):
            self.moves = format_string_to_moves(moves)
        else:
            self.moves = moves

    def __str__(self) -> str:
        return " ".join(self.moves).replace(") (", " ")

    def __repr__(self) -> str:
        return f'MoveSequence("{str(self)}")'

    def __hash__(self) -> int:
        return hash(str(self))

    def __len__(self) -> int:
        return count_length(self.moves, metric=METRIC)

    def __add__(self, other: MoveSequence | list[str]) -> MoveSequence:
        if isinstance(other, MoveSequence):
            return MoveSequence(self.moves + other.moves)
        elif isinstance(other, list):
            return MoveSequence(self.moves + other)

    def __radd__(self, other: MoveSequence | list[str]) -> MoveSequence:
        if isinstance(other, MoveSequence):
            return MoveSequence(other.moves + self.moves)
        elif isinstance(other, list):
            return MoveSequence(other + self.moves)

    def __eq__(self, other: MoveSequence) -> bool:
        return self.moves == other.moves

    def __ne__(self, other: MoveSequence) -> bool:
        return self.moves != other.moves

    def __getitem__(self, key: slice | int) -> MoveSequence | str:
        if isinstance(key, slice):
            return MoveSequence(self.moves[key])
        elif isinstance(key, int):
            return self.moves[key]

    def __iter__(self) -> Any:
        for move in self.moves:
            yield move

    def __contains__(self, item: str) -> bool:
        return item in self.moves

    def __bool__(self) -> bool:
        return bool(self.moves)

    def __copy__(self) -> MoveSequence:
        return MoveSequence(moves=self.moves.copy())

    def __lt__(self, other: MoveSequence | list[str]) -> bool:
        return len(self) < len(other)

    def __le__(self, other: MoveSequence | list[str]) -> bool:
        return len(self) <= len(other)

    def __gt__(self, other: MoveSequence | list[str]) -> bool:
        return len(self) > len(other)

    def __ge__(self, other: MoveSequence | list[str]) -> bool:
        return len(self) >= len(other)

    def __mul__(self, other: int) -> MoveSequence:
        return MoveSequence(self.moves * other)

    def __rmul__(self, other: int) -> MoveSequence:
        return MoveSequence(other * self.moves)

    def __reversed__(self) -> MoveSequence:
        return MoveSequence(list(reversed(self.moves)))

    def __invert__(self) -> MoveSequence:
        return MoveSequence(
            [invert_move(move) for move in reversed(self.moves)]
        )

    def apply_move_fn(self, fn: Callable) -> None:
        """Apply a function to each move.

        Args:
            fn (Callable): _description_
        """
        self.moves = list(itertools.chain(*[
            (
                ["(" + sub + ")" for sub in fn(move[1:-1]).split()]
                if move.startswith("(") else fn(move).split()
            )
            for move in self.moves
        ]))


def niss_sequence(sequence: MoveSequence) -> MoveSequence:
    """Niss a sequence."""
    return MoveSequence([niss_move(move) for move in sequence])


def unniss(sequence: MoveSequence) -> MoveSequence:
    """Unniss a move sequence."""

    normal_moves: list[str] = []
    inverse_moves: list[str] = []

    for move in sequence:
        if move.startswith("("):
            inverse_moves.append(strip_move(move))
        else:
            normal_moves.append(move)

    return MoveSequence(normal_moves) + ~MoveSequence(inverse_moves)


def replace_slice_moves(sequence: MoveSequence) -> None:
    """Inplace replace slice notation."""

    slice_mapping = {
        "E": ("U", "D'", "y'"),
        "M": ("L'", "R", "x'"),
        "S": ("F'", "B", "z"),
    }

    wide_pattern = re.compile(r"^([EMS])([2']?)$")

    def replace_match(match: re.Match) -> str:
        slice = match.group(1)
        turn_mod = match.group(2)
        first, second, rot = slice_mapping[slice]

        combined = f"{first}{turn_mod} {second}{turn_mod} {rot}{turn_mod}"
        return combined.replace("''", "").replace("'2", "2")

    sequence.apply_move_fn(
        fn=lambda move: wide_pattern.sub(replace_match, move)
    )


def replace_wide_moves(sequence: MoveSequence, size: int = CUBE_SIZE) -> None:
    """Inplace replace wide notation wider than size/2."""

    wide_mapping = {
        "R": ("L", "x", ""),
        "L": ("R", "x", "'"),
        "U": ("D", "y", ""),
        "D": ("U", "y", "'"),
        "F": ("B", "z", ""),
        "B": ("F", "z", "'"),
    }

    wide_pattern = re.compile(r"^([23456789]?)([LRFBUD])w([2']?)$")

    def replace_match(match: re.Match) -> str:
        wide = match.group(1) or "2"
        diff = size - int(wide)
        if diff >= size / 2:
            return match.string

        wide_mod = "w" if diff > 1 else ""
        diff_mod = str(diff) if diff > 2 else ""
        turn_mod = match.group(3)
        move = match.group(2)
        base, rot, rot_mod = wide_mapping[move]
        rot_mod = f"{rot_mod}{turn_mod}".replace("''", "").replace("'2", "2")

        if diff < 1:
            return f"{rot}{rot_mod}"
        return f"{diff_mod}{base}{wide_mod}{turn_mod} {rot}{rot_mod}"

    sequence.apply_move_fn(
        fn=lambda move: wide_pattern.sub(replace_match, move)
    )


def move_rotations_to_end(sequence: MoveSequence) -> MoveSequence:
    """Move all rotations to the end of the sequence."""

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
    """Combine adjacent moves if they cancel each other."""

    output_moves = []

    last_axis = None
    accumulated_moves = []
    for move in sequence:
        if is_rotation(move):
            if accumulated_moves:
                output_moves.extend(simplyfy_axis_moves(accumulated_moves))
                accumulated_moves = []
            output_moves.append(move)
            last_axis = None
            continue
        axis = get_axis(move)
        if axis == last_axis:
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
    """Decompose a move sequence into inverse and normal moves."""

    normal_moves: list[str] = []
    inverse_moves: list[str] = []

    for move in sequence:
        if move.startswith("("):
            inverse_moves.append(strip_move(move))
        else:
            normal_moves.append(move)

    return MoveSequence(normal_moves), MoveSequence(inverse_moves)


def cleanup(sequence: MoveSequence, size: int = CUBE_SIZE) -> MoveSequence:
    """
    Cleanup a sequence of moves by following these "rules":
    - Present normal moves before inverse moves
    - Replace slice notation with normal moves
    - Replace wide notation with normal moves
    - Move all rotations to the end of the sequence.
    - Combine the rotations such that you orient the up face and front face
    - Combine adjacent moves if they cancel each other, sorted lexically
    """
    normal_seq, inverse_seq = decompose(sequence)

    replace_wide_moves(normal_seq, size=size)
    replace_slice_moves(normal_seq)
    normal_seq = move_rotations_to_end(normal_seq)
    normal_seq = combine_axis_moves(normal_seq)

    replace_wide_moves(inverse_seq, size=size)
    replace_slice_moves(inverse_seq)
    inverse_seq = move_rotations_to_end(inverse_seq)
    inverse_seq = combine_axis_moves(inverse_seq)

    return normal_seq + niss_sequence(inverse_seq)


def main():
    raw_text = "(Fw\t R2 x (U2\nM')L2 Rw3 () F2  ( Bw 2 y' D' F')) // Comment"
    moves = remove_comment(raw_text)
    seq = MoveSequence(moves)
    print("\nMoves:", seq)
    print("Cleaned:", cleanup(seq))

    rotations = "x y2 z' x' y2 x2 z' y' x y2 x' z2 y' x2 z' y2"  # equals y
    print("\nRotations:", MoveSequence(rotations))
    print("Reduced:", move_rotations_to_end(MoveSequence(rotations)))

    axis_moves = "R R' L R2 U U2 L2 D2 D2 L2  U' B U' B' F B2"
    print("\nAxis moves:", MoveSequence(axis_moves))
    print("Combined:", combine_axis_moves(MoveSequence(axis_moves)))

    seq = "Rw L Bw2 Fw' D Rw2"
    print(MoveSequence(seq))
    print(replace_wide_moves(MoveSequence(seq)))


if __name__ == "__main__":
    main()
