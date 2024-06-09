from __future__ import annotations

from typing import Any

from rubiks_cube.utils.metrics import count_length
from rubiks_cube.utils.move import get_axis
from rubiks_cube.utils.move import invert_move
from rubiks_cube.utils.move import is_rotation
from rubiks_cube.utils.move import move_as_int
from rubiks_cube.utils.move import niss_move
from rubiks_cube.utils.move import repr_moves
from rubiks_cube.utils.move import rotate_move
from rubiks_cube.utils.move import string_to_moves
from rubiks_cube.utils.move import strip_move
from rubiks_cube.utils.formatter import format_string
from rubiks_cube.utils.formatter import remove_comment


class Sequence:
    """A move sequence for the Rubiks cube represented as a list of strings."""

    def __init__(self, moves: str | list[str] | None = None) -> None:
        if moves is None:
            self.moves = []
        elif isinstance(moves, str):
            moves_str = format_string(moves)
            self.moves = string_to_moves(moves_str)
        else:
            self.moves = moves

    def __str__(self) -> str:
        if not self.moves:
            return ""
        return repr_moves(self.moves)

    def __repr__(self) -> str:
        return f'{__class__}("{str(self)}")'

    def __len__(self) -> int:
        return count_length(self.moves)

    def __add__(self, other: Sequence | list[str]) -> Sequence:
        if isinstance(other, Sequence):
            return Sequence(self.moves + other.moves)
        elif isinstance(other, list):
            return Sequence(self.moves + other)

    def __radd__(self, other: Sequence | list[str]) -> Sequence:
        if isinstance(other, Sequence):
            return Sequence(other.moves + self.moves)
        elif isinstance(other, list):
            return Sequence(other + self.moves)

    def __eq__(self, other: Sequence) -> bool:
        return self.moves == other.moves

    def __ne__(self, other: Sequence) -> bool:
        return self.moves != other.moves

    def __getitem__(self, key: slice | int) -> Sequence | str:
        if isinstance(key, slice):
            return Sequence(self.moves[key])
        elif isinstance(key, int):
            return self.moves[key]

    def __iter__(self) -> Any:
        for move in self.moves:
            yield move

    def __contains__(self, item: str) -> bool:
        return item in self.moves

    def __bool__(self) -> bool:
        return bool(self.moves)

    def __copy__(self) -> Sequence:
        return Sequence(moves=self.moves.copy())

    def __lt__(self, other: Sequence | list[str]) -> bool:
        return len(self) < len(other)

    def __le__(self, other: Sequence | list[str]) -> bool:
        return len(self) <= len(other)

    def __gt__(self, other: Sequence | list[str]) -> bool:
        return len(self) > len(other)

    def __ge__(self, other: Sequence | list[str]) -> bool:
        return len(self) >= len(other)

    def __mul__(self, other: int) -> Sequence:
        return Sequence(self.moves * other)

    def __rmul__(self, other: int) -> Sequence:
        return Sequence(other * self.moves)

    def __reversed__(self) -> Sequence:
        return Sequence(list(reversed(self.moves)))

    def __invert__(self) -> Sequence:
        return Sequence([invert_move(move) for move in reversed(self.moves)])


def niss_sequence(sequence: Sequence) -> Sequence:
    """Niss a sequence."""
    return Sequence([niss_move(move) for move in sequence])


def unniss(sequence: Sequence) -> Sequence:
    """Unniss a sequence."""
    normal_moves = ""
    inverse_moves = ""

    for move in sequence:
        if move.startswith("("):
            inverse_moves += move
        else:
            normal_moves += move

    inverse_stripped = strip_move(inverse_moves)
    unnissed_inverse_moves = ~ Sequence(inverse_stripped)

    return Sequence(normal_moves) + unnissed_inverse_moves


def replace_slice_moves(sequence: Sequence) -> Sequence:
    """Replace slice notation with normal moves."""

    moves = []
    for move in sequence:
        match strip_move(move):
            case "M": moves.extend(["R", "L'", "x'"])
            case "M'": moves.extend(["R'", "L", "x"])
            case "M2": moves.extend(["R2", "L2", "x2"])
            case "E": moves.extend(["U", "D'", "y'"])
            case "E'": moves.extend(["U'", "D", "y"])
            case "E2": moves.extend(["U2", "D2", "y2"])
            case "S": moves.extend(["F'", "B", "z"])
            case "S'": moves.extend(["F", "B'", "z'"])
            case "S2": moves.extend(["F2", "B2", "z2"])
            case _:
                moves.append(move)
                continue
        if move.startswith("("):
            moves[-1] = "(" + moves[-1] + ")"

    return Sequence(moves)


def replace_wide_moves(sequence: Sequence) -> Sequence:
    """Replace wide notation with normal moves + rotation."""

    moves = []
    for move in sequence:
        match strip_move(move):
            case "Rw": moves.extend(["L", "x"])
            case "Rw'": moves.extend(["L'", "x'"])
            case "Rw2": moves.extend(["L2", "x2"])
            case "Lw": moves.extend(["R", "x'"])
            case "Lw'": moves.extend(["R'", "x"])
            case "Lw2": moves.extend(["R2", "x2"])
            case "Uw": moves.extend(["D", "y"])
            case "Uw'": moves.extend(["D'", "y'"])
            case "Uw2": moves.extend(["D2", "y2"])
            case "Dw": moves.extend(["U", "y'"])
            case "Dw'": moves.extend(["U'", "y"])
            case "Dw2": moves.extend(["U2", "y2"])
            case "Fw": moves.extend(["B", "z"])
            case "Fw'": moves.extend(["B'", "z'"])
            case "Fw2": moves.extend(["B2", "z2"])
            case "Bw": moves.extend(["F", "z'"])
            case "Bw'": moves.extend(["F'", "z"])
            case "Bw2": moves.extend(["F2", "z2"])
            case _:
                moves.extend([move])
                continue
        if move.startswith("("):
            moves[-1] = "(" + moves[-1] + ")"

    return Sequence(moves)


def move_rotations_to_end(sequence: Sequence) -> Sequence:
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

    return Sequence(output_list) + standard_rotation


def combine_rotations(rotation_list: list[str]) -> list[str]:
    """
    Collapse rotations in a sequence to a standard rotation.
    It rotates the cube to correct up-face and the correct front-face.
    """
    standard_rotations = {
        "UF": "",
        "UL": "y'",
        "UB": "y2",
        "UR": "y",
        "FU": "x y2",
        "FL": "x y'",
        "FD": "x",
        "FR": "x y",
        "RU": "z' y'",
        "RF": "z'",
        "RD": "z' y",
        "RB": "z' y2",
        "BU": "x'",
        "BL": "x' y'",
        "BD": "x' y2",
        "BR": "x' y",
        "LU": "z y",
        "LF": "z",
        "LD": "z y'",
        "LB": "z y2",
        "DF": "z2",
        "DL": "x2 y'",
        "DB": "x2",
        "DR": "x2 y",
    }
    transition_dict = {
        'x': {
            'UF': 'FD',
            'UL': 'LD',
            'UB': 'BD',
            'UR': 'RD',
            'FU': 'UB',
            'FL': 'LB',
            'FD': 'DB',
            'FR': 'RB',
            'RU': 'UL',
            'RF': 'FL',
            'RD': 'DL',
            'RB': 'BL',
            'BU': 'UF',
            'BL': 'LF',
            'BD': 'DF',
            'BR': 'RF',
            'LU': 'UR',
            'LF': 'FR',
            'LD': 'DR',
            'LB': 'BR',
            'DF': 'FU',
            'DL': 'LU',
            'DB': 'BU',
            'DR': 'RU',
        },
        "x'": {
            'UF': 'BU',
            'UL': 'RU',
            'UB': 'FU',
            'UR': 'LU',
            'FU': 'DF',
            'FL': 'RF',
            'FD': 'UF',
            'FR': 'LF',
            'RU': 'DR',
            'RF': 'BR',
            'RD': 'UR',
            'RB': 'FR',
            'BU': 'DB',
            'BL': 'RB',
            'BD': 'UB',
            'BR': 'LB',
            'LU': 'DL',
            'LF': 'BL',
            'LD': 'UL',
            'LB': 'FL',
            'DF': 'BD',
            'DL': 'RD',
            'DB': 'FD',
            'DR': 'LD',
        },
        'x2': {
            'UF': 'DB',
            'UL': 'DR',
            'UB': 'DF',
            'UR': 'DL',
            'FU': 'BD',
            'FL': 'BR',
            'FD': 'BU',
            'FR': 'BL',
            'RU': 'LD',
            'RF': 'LB',
            'RD': 'LU',
            'RB': 'LF',
            'BU': 'FD',
            'BL': 'FR',
            'BD': 'FU',
            'BR': 'FL',
            'LU': 'RD',
            'LF': 'RB',
            'LD': 'RU',
            'LB': 'RF',
            'DF': 'UB',
            'DL': 'UR',
            'DB': 'UF',
            'DR': 'UL',
        },
        'y': {
            'UF': 'UR',
            'UL': 'UF',
            'UB': 'UL',
            'UR': 'UB',
            'FU': 'FL',
            'FL': 'FD',
            'FD': 'FR',
            'FR': 'FU',
            'RU': 'RF',
            'RF': 'RD',
            'RD': 'RB',
            'RB': 'RU',
            'BU': 'BR',
            'BL': 'BU',
            'BD': 'BL',
            'BR': 'BD',
            'LU': 'LB',
            'LF': 'LU',
            'LD': 'LF',
            'LB': 'LD',
            'DF': 'DL',
            'DL': 'DB',
            'DB': 'DR',
            'DR': 'DF',
        },
        "y'": {
            'UF': 'UL',
            'UL': 'UB',
            'UB': 'UR',
            'UR': 'UF',
            'FU': 'FR',
            'FL': 'FU',
            'FD': 'FL',
            'FR': 'FD',
            'RU': 'RB',
            'RF': 'RU',
            'RD': 'RF',
            'RB': 'RD',
            'BU': 'BL',
            'BL': 'BD',
            'BD': 'BR',
            'BR': 'BU',
            'LU': 'LF',
            'LF': 'LD',
            'LD': 'LB',
            'LB': 'LU',
            'DF': 'DR',
            'DL': 'DF',
            'DB': 'DL',
            'DR': 'DB',
        },
        'y2': {
            'UF': 'UB',
            'UL': 'UR',
            'UB': 'UF',
            'UR': 'UL',
            'FU': 'FD',
            'FL': 'FR',
            'FD': 'FU',
            'FR': 'FL',
            'RU': 'RD',
            'RF': 'RB',
            'RD': 'RU',
            'RB': 'RF',
            'BU': 'BD',
            'BL': 'BR',
            'BD': 'BU',
            'BR': 'BL',
            'LU': 'LD',
            'LF': 'LB',
            'LD': 'LU',
            'LB': 'LF',
            'DF': 'DB',
            'DL': 'DR',
            'DB': 'DF',
            'DR': 'DL',
        },
        'z': {
            'UF': 'LF',
            'UL': 'BL',
            'UB': 'RB',
            'UR': 'FR',
            'FU': 'RU',
            'FL': 'UL',
            'FD': 'LD',
            'FR': 'DR',
            'RU': 'BU',
            'RF': 'UF',
            'RD': 'FD',
            'RB': 'DB',
            'BU': 'LU',
            'BL': 'DL',
            'BD': 'RD',
            'BR': 'UR',
            'LU': 'FU',
            'LF': 'DF',
            'LD': 'BD',
            'LB': 'UB',
            'DF': 'RF',
            'DL': 'FL',
            'DB': 'LB',
            'DR': 'BR',
        },
        "z'": {
            'UF': 'RF',
            'UL': 'FL',
            'UB': 'LB',
            'UR': 'BR',
            'FU': 'LU',
            'FL': 'DL',
            'FD': 'RD',
            'FR': 'UR',
            'RU': 'FU',
            'RF': 'DF',
            'RD': 'BD',
            'RB': 'UB',
            'BU': 'RU',
            'BL': 'UL',
            'BD': 'LD',
            'BR': 'DR',
            'LU': 'BU',
            'LF': 'UF',
            'LD': 'FD',
            'LB': 'DB',
            'DF': 'LF',
            'DL': 'BL',
            'DB': 'RB',
            'DR': 'FR',
        },
        'z2': {
            'UF': 'DF',
            'UL': 'DL',
            'UB': 'DB',
            'UR': 'DR',
            'FU': 'BU',
            'FL': 'BL',
            'FD': 'BD',
            'FR': 'BR',
            'RU': 'LU',
            'RF': 'LF',
            'RD': 'LD',
            'RB': 'LB',
            'BU': 'FU',
            'BL': 'FL',
            'BD': 'FD',
            'BR': 'FR',
            'LU': 'RU',
            'LF': 'RF',
            'LD': 'RD',
            'LB': 'RB',
            'DF': 'UF',
            'DL': 'UL',
            'DB': 'UB',
            'DR': 'UR',
        }
    }

    current_state = "UF"
    for rotation in rotation_list:
        current_state = transition_dict[rotation][current_state]

    standard_rotation_list = standard_rotations[current_state]

    return standard_rotation_list.split()


def combine_axis_moves(sequence: Sequence) -> Sequence:
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

    output_sequence = Sequence(output_moves)

    if output_sequence == sequence:
        return output_sequence
    return combine_axis_moves(output_sequence)


def simplyfy_axis_moves(moves: list[str]) -> list[str]:
    """
    Combine adjacent moves if they cancel each other.
    E.g. R R' -> "", R L R' -> L
    """
    moves.sort()

    face_count = {}

    for move in moves:
        face = move[0]
        if face in face_count:
            face_count[face] += move_as_int(move)
        else:
            face_count[face] = move_as_int(move)

    return [
        ["", f"{face}", f"{face}2", f"{face}'"][face_count[face] % 4]
        for face in face_count.keys()
        if face_count[face] % 4 != 0
    ]


def split_normal_inverse(sequence: Sequence) -> tuple[Sequence, Sequence]:
    """Split a cleaned sequence into inverse and normal moves."""

    normal_moves: list[str] = []
    inverse_moves: list[str] = []

    for move in sequence:
        if move.startswith("("):
            inverse_moves.append(strip_move(move))
        else:
            normal_moves.append(move)

    return Sequence(normal_moves), Sequence(inverse_moves)


def cleanup(sequence: Sequence) -> Sequence:
    """
    Cleanup a sequence of moves by following these "rules":
    - Present normal moves before inverse moves
    - Replace slice notation with normal moves
    - Replace wide notation with normal moves
    - Move all rotations to the end of the sequence.
    - Combine the rotations such that you orient the up face and front face
    - Combine adjacent moves if they cancel each other, sorted lexically
    """
    normal_moves, inverse_moves = split_normal_inverse(sequence)

    normal_seq = replace_slice_moves(normal_moves)
    normal_seq = replace_wide_moves(normal_seq)
    normal_seq = move_rotations_to_end(normal_seq)
    normal_seq = combine_axis_moves(normal_seq)

    inverse_seq = replace_slice_moves(inverse_moves)
    inverse_seq = replace_wide_moves(inverse_seq)
    inverse_seq = move_rotations_to_end(inverse_seq)
    inverse_seq = combine_axis_moves(inverse_seq)

    return normal_seq + niss_sequence(inverse_seq)


def main():
    raw_text = "(Fw\t R2 x (U2\nM')L2 Rw3 () F2  ( Bw 2 y' D' F')) // Comment"
    moves = remove_comment(raw_text)
    seq = Sequence(moves)
    print("\nMoves:", seq)
    print("Cleaned:", cleanup(seq))

    rotations = "x y2 z' x' y2 x2 z' y' x y2 x' z2 y' x2 z' y2"  # equals y
    print("\nRotations:", Sequence(rotations))
    print("Standard rotations:", move_rotations_to_end(Sequence(rotations)))

    axis_moves = "R R' L R2 U U2 L2 D2 D2 L2  U' B U' B' F B2"
    print("\nAxis moves:", Sequence(axis_moves))
    print("Combined axis moves:", combine_axis_moves(Sequence(axis_moves)))


if __name__ == "__main__":
    main()
