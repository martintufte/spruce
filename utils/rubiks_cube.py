import re
import numpy as np
from .permutations import (
    get_permutations,
    count_solved,
    corner_cycle,
    edge_cycle,
    SOLVED
)

PERMUTATIONS = get_permutations(3)


class Sequence:
    """A sequence of moves for the Rubiks cube."""

    def __init__(self, moves: str = ""):
        self.moves = format_sequence(moves)

    def __str__(self):
        return self.moves

    def __repr__(self):
        if self.moves:
            return f'Sequence("{self.moves}")'
        return "Sequence()"

    def __add__(self, other):
        if isinstance(other, Sequence):
            return Sequence(self.moves + " " + other.moves)
        elif isinstance(other, str):
            return Sequence(self.moves + " " + other)
        raise TypeError("Invalid type!")

    def __radd__(self, other):
        if isinstance(other, Sequence):
            return Sequence(other.moves + " " + self.moves)
        elif isinstance(other, str):
            return Sequence(other + " " + self.moves)
        raise TypeError("Invalid type!")

    def __len__(self):
        return count_length(self.moves)

    def __eq__(self, other):
        return self.moves == other.moves

    def __ne__(self, other):
        return self.moves != other.moves

    def __getitem__(self, key):
        return Sequence(self.moves.split()[key])

    def __iter__(self):
        niss = False
        for move in self.moves.split():
            stripped_move = move.replace("(", "").replace(")", "")
            if move.startswith("("):
                niss = not niss
            yield "(" + stripped_move + ")" if niss else stripped_move
            if move.endswith(")"):
                niss = not niss

    def __contains__(self, item):
        return item in self.moves

    def __bool__(self):
        return bool(self.moves)

    def __copy__(self):
        return Sequence(self.moves)

    def __deepcopy__(self, memo):
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
        return Sequence(" ".join([self.moves] * other))

    def __rmul__(self, other):
        return Sequence(" ".join([self.moves] * other))

    def __reversed__(self):
        return Sequence(" ".join(reversed(self.moves.split())))

    def __invert__(self):
        return Sequence(self.invert())

    def invert(self):
        """Invert a sequence."""
        inv_list = []
        for move in reversed(self.moves.split()):
            if move.endswith("'"):
                inv_list.append(move[:-1])
            elif move.endswith("2"):
                inv_list.append(move)
            else:
                inv_list.append(move + "'")
        return " ".join(inv_list)


def is_valid_symbols(input_string: str) -> bool:
    """Check that a string only contains valid symbols."""

    return all(
        char in "RLFBUDMESrlfbudxyzw2' ()/\t\n" for char in input_string
    )


def split_into_moves_comment(input_string: str) -> tuple[str, str]:
    """Split a sequence into moves and comment."""

    idx = input_string.find("//")

    if idx == -1:
        moves, comment = input_string, ""
    else:
        moves, comment = input_string[:idx], input_string[(idx+2):]

    return moves, comment.strip()


def remove_redundant_parenteses(input_string: str) -> str:
    """Remove redundant moves in a sequence."""

    # Remove redundant parentheses
    output_string = input_string
    while True:
        output_string = re.sub(r"\(\s*\)", "", output_string)
        output_string = re.sub(r"\)\s*\(", "", output_string)
        if output_string == input_string:
            break
        input_string = output_string

    return output_string


def format_parenteses(input_string: str) -> str:
    """Check parenteses balance and alternate parenteses."""

    # Check if all parentheses are balanced and
    # alternate between normal and inverse parentheses
    stack = []
    output_string = ""
    for char in input_string:
        if char == "(":
            stack.append(char)
            output_string += "(" if len(stack) % 2 else ")"
        elif char == ")":
            if not stack:
                raise ValueError("Unbalanced parentheses!")
            stack.pop()
            output_string += "(" if len(stack) % 2 else ")"
        else:
            output_string += char
    if stack:
        raise ValueError("Unbalanced parentheses!")

    return remove_redundant_parenteses(output_string)


def format_whitespaces(input_string: str):
    """Format whitespaces in a sequence."""

    # Add extra space before starting moves
    input_string = re.sub(r"([RLFBUDMESxyz])", r" \1", input_string)

    # Add space before and after parentheses
    input_string = re.sub(r"(\()", r" \1", input_string)
    input_string = re.sub(r"(\))", r"\1 ", input_string)

    # Remove extra spaces
    input_string = re.sub(r"\s+", " ", input_string)

    # Remove spaces before and after parentheses
    input_string = re.sub(r"\s+\)", ")", input_string)
    input_string = re.sub(r"\(\s+", "(", input_string)

    # Remove spaces before wide moves, apostrophes and double moves
    input_string = re.sub(r"\s+w", "w", input_string)
    input_string = re.sub(r"\s+2", "2", input_string)
    input_string = re.sub(r"\s+'", "'", input_string)

    return input_string.strip()


def replace_old_wide_notation(input_string: str):
    """Replace old wide notation with new wide notation."""
    replace_dict = {
        "Uw": "u",
        "Dw": "d",
        "Fw": "f",
        "Bw": "b",
        "Lw": "l",
        "Rw": "r",
    }
    for new, old in replace_dict.items():
        input_string = input_string.replace(old, new)
    return input_string


def is_valid_moves(input_string: str):
    """Check if a string is valid Rubik's Cube notation."""

    # Remove comments and parentheses
    moves, _ = split_into_moves_comment(input_string)
    moves = moves.replace("(", "").replace(")", "")

    # Check if the sequence has correct moves
    pattern = r"^[RLFBUD][w][2']?$|^[RLUDFBxyzMESrludfb][2']?$"

    return all(re.match(pattern, move) for move in Sequence(moves))


def format_sequence(input_string: str) -> str:
    """Format a string for Rubiks Cube."""

    # Assume that the input string is valid Rubik's Cube notation
    # Assume that there are no comments in the input string

    input_string = replace_old_wide_notation(input_string)
    input_string = format_parenteses(input_string)
    input_string = format_whitespaces(input_string)

    return input_string


# TODO: Check if this is correct
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
                moves.extend([move])
                continue
        # Add parentheses if niss
        if move.startswith("("):
            moves[-1] = "(" + moves[-1] + ")"
    return Sequence(" ".join(moves))


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

    return Sequence(" ".join(moves))


# TODO: Fix this piece of code
def move_rotations_to_end(sequence: Sequence) -> Sequence:
    """Move all rotations to the end of the sequence."""

    return sequence


# TODO: Fix this piece of code
def combine_adjacent_moves(sequence: Sequence) -> Sequence:
    """Combine adjacent moves if they cancel each other."""

    return sequence


# TODO: Fix this piece of code
def cleanup(sequence: Sequence) -> Sequence:
    """Cleanup a sequence."""
    normal_moves = ""
    inverse_moves = ""

    for move in sequence:
        if move.startswith("("):
            inverse_moves += move
        else:
            normal_moves += move

    # Standardize slice notation, wide notation and rotations
    normal_seq = replace_slice_moves(Sequence(normal_moves))
    normal_seq = replace_wide_moves(normal_seq)
    normal_seq = move_rotations_to_end(normal_seq)
    normal_seq = combine_adjacent_moves(normal_seq)

    inverse_seq = replace_slice_moves(Sequence(inverse_moves))
    inverse_seq = replace_wide_moves(inverse_seq)
    inverse_seq = move_rotations_to_end(inverse_seq)
    inverse_seq = combine_adjacent_moves(inverse_seq)

    return normal_seq + inverse_seq


# TODO: Fix this piece of code
def split_normal_inverse(sequence: Sequence) -> tuple[Sequence, Sequence]:
    """Split a cleaned sequence into inverse and normal moves."""

    if "(" in sequence:
        idx = sequence.moves.find("(")
        normal_moves = sequence.moves[:idx].strip()
        inverse_moves = sequence.moves[idx:].strip()
        return Sequence(normal_moves), Sequence(inverse_moves)
    return sequence, Sequence()


def count_length(moves, count_rotations=False, metric="HTM"):
    """Count the length of a sequence."""

    moves = moves.replace("(", "").replace(")", "").strip()

    sum_rotations = sum(1 for char in moves if char in "xyz")
    sum_slices = sum(1 for char in moves if char in "MES")
    sum_double_moves = sum(1 for char in moves if char in "2")
    sum_moves = len(moves.split())

    if not count_rotations:
        sum_moves -= sum_rotations

    if metric == "HTM":
        return sum_moves + sum_slices
    elif metric == "STM":
        return sum_moves
    elif metric == "QTM":
        return sum_moves + sum_double_moves

    raise ValueError(f"Invalid metric: {metric}")


def debug_cube_state(cube_state):
    """Get a debug text for a scramble."""
    p = cube_state.get_permutation()

    text = "EO count: (F/B: ?, R/L: ?, U/D: ?)  \n"
    text += f"Blind trace: {corner_cycle(p)} {edge_cycle(p)}  \n"
    text += f"Number of solved pieces: {count_solved(p)}  \n"

    return text


def get_cube_permutation(sequence: Sequence) -> np.ndarray:
    """Get a cube permutation."""

    perm = np.copy(SOLVED)

    for move in sequence:
        if move.startswith("("):
            raise ValueError("Cannot get cube permutation of niss!")
        perm = perm[PERMUTATIONS[move]]

    return perm


def apply_moves(permutation, sequence: Sequence):
    """Apply a sequence of moves to the permutation."""
    for move in sequence:
        permutation = permutation[PERMUTATIONS[move]]

    return permutation


if __name__ == "__main__":

    raw_text = "(Fw\t R2 x (U2\n M'    )L2 Rw2 () F2  ( Bw 2 y' D' F'))"

    moves, comment = split_into_moves_comment(raw_text)
    seq = Sequence(moves)

    print(repr(seq))
    print("Length of seq:", len(seq))
    print("Unnissed:", unniss(seq))
    print("Cleaned:", cleanup(seq))
