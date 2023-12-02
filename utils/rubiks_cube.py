import numpy as np
from utils import default
from utils.permutations import (
    get_permutations,
    SOLVED
)
from utils.string_formatting import (
    format_string,
    invert_move,
    niss_move,
    split_into_moves_comment,
    is_rotation,
    apply_rotation,
    get_axis,
    repr_moves,
)

PERMUTATIONS = get_permutations(3)


class Sequence:
    """
    A sequence of moves for the Rubiks cube.
    The sequence is represented as a list.
    """

    def __init__(self, moves: str | list[str] = []):
        """Initialize a sequence of moves."""
        if isinstance(moves, str):
            self.moves = format_string(moves)
        else:
            self.moves = moves

    def __str__(self):
        if not self.moves:
            return ""
        return repr_moves(self.moves)

    def __repr__(self):
        return f'Sequence("{str(self)}")'

    def __len__(self):
        return count_length(self)

    def __add__(self, other):
        if isinstance(other, Sequence):
            return Sequence(self.moves + other.moves)
        elif isinstance(other, list):
            return Sequence(self.moves + other)
        raise TypeError("Invalid type!")

    def __radd__(self, other):
        if isinstance(other, Sequence):
            return Sequence(other.moves + self.moves)
        elif isinstance(other, list):
            return Sequence(other + self.moves)
        raise TypeError("Invalid type!")

    def __eq__(self, other):
        if isinstance(other, Sequence):
            return self.moves == other.moves
        elif isinstance(other, list):
            return self.moves == other
        raise TypeError("Invalid type!")

    def __ne__(self, other):
        if isinstance(other, Sequence):
            return self.moves != other.moves
        elif isinstance(other, list):
            return self.moves != other
        raise TypeError("Invalid type!")

    def __getitem__(self, key):
        if isinstance(key, slice):
            return Sequence(self.moves[key])
        elif isinstance(key, int):
            return self.moves[key]
        raise TypeError("Invalid type!")

    def __iter__(self):
        for move in self.moves:
            yield move

    def __contains__(self, item):
        return item in self.moves

    def __bool__(self):
        return bool(self.moves)

    def __copy__(self):
        return Sequence(self.moves)

    def __lt__(self, other):
        return len(self) < len(other)

    def __le__(self, other):
        return len(self) <= len(other)

    def __gt__(self, other):
        return len(self) > len(other)

    def __ge__(self, other):
        return len(self) >= len(other)

    def __mul__(self, other):
        if isinstance(other, int):
            return Sequence(self.moves * other)
        raise TypeError("Invalid type!")

    def __rmul__(self, other):
        if isinstance(other, int):
            return Sequence(other * self.moves)
        raise TypeError("Invalid type!")

    def __reversed__(self):
        return Sequence(list(reversed(self.moves)))

    def __invert__(self):
        return self.invert()

    def invert(self):
        """Invert a sequence."""
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

    inverse_stripped = inverse_moves.replace("(", "").replace(")", "")
    unnissed_inverse_moves = ~ Sequence(inverse_stripped)

    return Sequence(normal_moves) + unnissed_inverse_moves


def replace_slice_moves(sequence: Sequence) -> Sequence:
    """Replace slice notation with normal moves."""
    moves = []
    for move in sequence:
        match move.replace("(", "").replace(")", ""):
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
        # Add parentheses if niss
        if move.startswith("("):
            moves[-1] = "(" + moves[-1] + ")"
    return Sequence(moves)


def replace_wide_moves(sequence: Sequence) -> Sequence:
    """Replace wide notation with normal moves + rotation."""
    moves = []
    for move in sequence:
        match move.replace("(", "").replace(")", ""):
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
        # Add parentheses if niss
        if move.startswith("("):
            moves[-1] = "(" + moves[-1] + ")"

    return Sequence(moves)


def move_rotations_to_end(
        sequence: Sequence,
        ) -> Sequence:
    """Move all rotations to the end of the sequence."""

    # Assume that the sequence is a list of moves
    rotation_list = []
    output_list = []

    for i, move in enumerate(sequence):
        if is_rotation(move):
            rotation_list.append(move)
        else:
            for rotation in reversed(rotation_list):
                move = apply_rotation(move, rotation)
            output_list.append(move)

    output_list.extend(rotation_list)

    return Sequence(output_list)


def combine_axis_moves(sequence: Sequence) -> Sequence:
    """Combine adjacent moves if they cancel each other."""

    axis_dict = {
        "R": {"R": "R2", "R'": " ", "R2": "R'"},
        "R'": {"R": " ", "R'": "R2", "R2": "R"},
        "R2": {"R": "R'", "R'": "R", "R2": " "},
        "L": {"L": "L2", "L'": " ", "L2": "L'"},
        "L'": {"L": " ", "L'": "L2", "L2": "L"},
        "L2": {"L": "L'", "L'": "L", "L2": " "},
        "U": {"U": "U2", "U'": " ", "U2": "U'"},
        "U'": {"U": " ", "U'": "U2", "U2": "U"},
        "U2": {"U": "U'", "U'": "U", "U2": " "},
        "D": {"D": "D2", "D'": " ", "D2": "D'"},
        "D'": {"D": " ", "D'": "D2", "D2": "D"},
        "D2": {"D": "D'", "D'": "D", "D2": " "},
        "F": {"F": "F2", "F'": " ", "F2": "F'"},
        "F'": {"F": " ", "F'": "F2", "F2": "F"},
        "F2": {"F": "F'", "F'": "F", "F2": " "},
        "B": {"B": "B2", "B'": " ", "B2": "B'"},
        "B'": {"B": " ", "B'": "B2", "B2": "B"},
        "B2": {"B": "B'", "B'": "B", "B2": " "},
    }

    output_list = []

    current_axis = None
    for move in sequence:
        if is_rotation(move):
            continue
        axis = get_axis(move)
        # same axis
        if axis == default(current_axis, axis):
            if not output_list:
                output_list.append(move)
            else:
                last_move = output_list[-1]
                new_move = axis_dict[last_move].get(move, move)
                if new_move == " ":
                    continue
                elif new_move == last_move:
                    output_list.append(last_move)
                    output_list.append(move)
                else:
                    output_list.append(new_move)

    output_sequence = Sequence(output_list)

    if output_sequence == sequence:
        return output_sequence
    return combine_axis_moves(output_sequence)


# TODO: Make this work!
def collapse_rotations(sequence: Sequence) -> Sequence:
    """Collapse rotations in a sequence."""

    # rotation of rotations
    rotation_rotaion_dict = {
        " ": {},
        "x": {
            " ": "x",
            "x": "x2", "x'": " ", "x2": "x'",
            "y": "z'", "y'": "z", "y2": "z2",
            "z": "y", "z'": "y'", "z2": "y2",
        },
        "x2": {
            " ": "x2",
            "x": "x'", "x'": "x", "x2": " ",
            "y": "y'", "y'": "y", "y2": "y2",
            "z": "z'", "z'": "z", "z2": "z2",
        },
        "x'": {
            " ": "x'",
            "x": " ", "x'": "x2", "x2": "x",
            "y": "z", "y'": "z", "y2": "z2",
            "z": "y'", "z'": "y", "z2": "y2",
        },
        "y": {
            " ": "y",
            "y": "y2", "y'": " ", "y2": "y'",
            "x": "z", "x'": "z'", "x2": "z2",
            "z": "x'", "z'": "x", "z2": "x2",
        },
        "y2": {
            " ": "y2",
            "y": "y'", "y'": "y", "y2": " ",
            "x": "x'", "x'": "x", "x2": "x2",
            "z": "z'", "z'": "z", "z2": "z2",
        },
        "y'": {
            " ": "y'",
            "y": " ", "y'": "y2", "y2": "y",
            "x": "z'", "x'": "z", "x2": "z2",
            "z": "x", "z'": "x'", "z2": "x2",
        },
        "z": {
            " ": "z",
            "z": "z2", "z'": " ", "z2": "z'",
            "x": "y'", "x'": "y", "x2": "y2",
            "y": "x", "y'": "x", "y2": "x2",
        },
        "z2": {
            " ": "z2",
            "z": "z'", "z'": "z", "z2": "",
            "x": "x'", "x'": "x", "x2": "x2",
            "y": "x'", "y'": "y", "y2": "y2",
        },
        "z'": {
            " ": "z'",
            "z": " ", "z'": "z2", "z2": "z",
            "x": "y", "x'": "y'", "x2": "y2",
            "y": "x'", "y'": "x'", "y2": "x2",
        },
    }

    # Assume that the sequence is a list of moves
    rotation_list = []
    output_list = []

    for i, move in enumerate(sequence):
        if is_rotation(move):
            rotation_list.append(move)
        else:
            for rotation in reversed(rotation_list):
                move = apply_rotation(move, rotation)
            output_list.append(move)

    return Sequence(output_list)


def cleanup(sequence: Sequence) -> Sequence:
    """Cleanup a sequence."""
    normal_moves, inverse_moves = split_normal_inverse(sequence)

    # Standardize slice notation, wide notation and rotations
    normal_seq = replace_slice_moves(normal_moves)
    normal_seq = replace_wide_moves(normal_seq)
    normal_seq = move_rotations_to_end(normal_seq)
    # normal_seq = combine_axis_moves(normal_seq)

    inverse_seq = replace_slice_moves(inverse_moves)
    inverse_seq = replace_wide_moves(inverse_seq)
    inverse_seq = move_rotations_to_end(inverse_seq)
    # inverse_seq = combine_axis_moves(inverse_seq)

    return normal_seq + niss_sequence(inverse_seq)


def split_normal_inverse(sequence: Sequence) -> tuple[Sequence, Sequence]:
    """Split a cleaned sequence into inverse and normal moves."""

    normal_moves = []
    inverse_moves = []

    for move in sequence:
        if move.startswith("("):
            inverse_moves.append(move.replace("(", "").replace(")", ""))
        else:
            normal_moves.append(move)

    return Sequence(normal_moves), Sequence(inverse_moves)


def count_length(seq: Sequence, count_rotations=False, metric="HTM"):
    """Count the length of a sequence."""
    move_string = str(seq)

    sum_rotations = sum(1 for char in move_string if char in "xyz")
    sum_slices = sum(1 for char in move_string if char in "MES")
    sum_double_moves = sum(1 for char in move_string if char in "2")
    sum_moves = len(move_string.split())

    if not count_rotations:
        sum_moves -= sum_rotations

    if metric == "HTM":
        return sum_moves + sum_slices
    elif metric == "STM":
        return sum_moves
    elif metric == "QTM":
        return sum_moves + sum_double_moves

    raise ValueError(f"Invalid metric: {metric}")


def get_cube_permutation(
        sequence: Sequence,
        ignore_rotations: bool = False,
) -> np.ndarray:
    """Get a cube permutation."""

    permutation = np.copy(SOLVED)

    for move in sequence:
        if move.startswith("("):
            raise ValueError("Cannot get cube permutation of niss!")
        elif ignore_rotations and is_rotation(move):
            continue
        else:
            permutation = permutation[PERMUTATIONS[move]]

    return permutation


def apply_moves(permutation, sequence: Sequence):
    """Apply a sequence of moves to the permutation."""
    for move in sequence:
        permutation = permutation[PERMUTATIONS[move]]

    return permutation


if __name__ == "__main__":

    raw_text = "(Fw\t R2 x (U2\nM')L2 Rw2 () F2  ( Bw 2 y' D' F')) // Comment"

    moves, comment = split_into_moves_comment(raw_text)

    seq = Sequence(moves)

    print("Length of seq:", len(seq))
    print("Unnissed:", unniss(seq))
    print("Cleaned:", cleanup(seq))
