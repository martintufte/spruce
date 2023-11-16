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
        self.moves = moves

    def __str__(self):
        return self.moves

    def __repr__(self):
        if self.moves:
            return f'Sequence("{self.moves}")'
        return "Sequence()"

    def __add__(self, other):
        return Sequence(self.moves + " " + other.moves)

    def __radd__(self, other):
        return Sequence(other.moves + " " + self.moves)

    def __len__(self):
        return count_length(self.moves)

    def __eq__(self, other):
        return self.moves == other.moves

    def __ne__(self, other):
        return self.moves != other.moves

    def __getitem__(self, key):
        return Sequence(self.moves.split()[key])

    def __iter__(self):
        for move in self.moves.split():
            yield move

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

    def __abs__(self):
        return len(self)

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


def is_valid_rubiks_cube_symbols(input_string: str) -> bool:
    """Check that a string only contains valid symbols."""

    return all(
        char in "RLFBUDMESrlfbudxyzw2' ()/\t\n" for char in input_string
    )


def split_into_sequence_comment(input_string: str) -> tuple[Sequence, str]:
    """Split a sequence into moves and comment."""

    # Remove comments
    if "//" not in input_string:
        seq = input_string
        comment = ""
    else:
        seq = input_string.split("//")[0]
        comment = "//".join(input_string.split("//")[1:])

    return Sequence(seq.strip()), comment.strip()


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


def is_valid_rubiks_cube_moves(input_string: str):
    """Check if a string is valid Rubik's Cube notation."""

    # Remove comments and parentheses
    seq, _ = split_into_sequence_comment(input_string)
    seq.moves = seq.moves.replace("(", "").replace(")", "")

    # Check if the sequence has correct moves
    pattern = r"^[RLFBUD][w][2']?$|^[RLUDFBxyzMESrludfb][2']?$"

    return all(re.match(pattern, move) for move in seq)


def validate_sequence(input_string: str) -> tuple[Sequence, str]:
    """Validate a string for Rubiks Cube."""
    seq, comment = split_into_sequence_comment(input_string)

    assert is_valid_rubiks_cube_symbols(seq.moves), (
        "Invalid symbols in sequence!"
    )

    seq.moves = replace_old_wide_notation(seq.moves)
    seq.moves = format_whitespaces(seq.moves)

    assert is_valid_rubiks_cube_moves(seq.moves), (
        "Invalid Rubik's Cube moves!"
    )

    return seq, comment


def split_sequence(sequence: Sequence) -> tuple[Sequence, Sequence]:
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
        perm = perm[PERMUTATIONS[move]]

    return perm


def apply_moves(permutation, sequence: Sequence):
    """Apply a sequence of moves to the permutation."""
    for move in sequence:
        permutation = permutation[PERMUTATIONS[move]]

    return permutation


''' UNUSED
class CubeState:
    """A cube state."""
    def __init__(self, sequence=""):
        self.sequence = sequence
        self.permutation = get_cube_permutation(sequence)

        self.draw = True
        self.debug = False
        self.unniss = True
        self.cleanup = True
        self.invert = False

    def apply_moves(self, new_sequence):
        """Apply a sequence of moves to the cube state."""
        for move in new_sequence.strip().split():
            self.permutation = self.permutation[PERMUTATIONS[move]]
        self.sequence += (
            " " + new_sequence if self.sequence else new_sequence
        )

    def get_sequence(self):
        """Get the sequence."""
        return self.sequence

    def get_permutation(self):
        """Get the permutation."""
        return self.permutation

    def from_sequence(self, sequence: Union[str, list[str]]):
        """Set the sequence and permutation."""
        if isinstance(sequence, list):
            sequence = " ".join(sequence)
        self.sequence = sequence
        self.permutation = get_cube_permutation(sequence)
'''

if __name__ == "__main__":

    raw_text = " R2(\t x' \nU2b)L 'D w \t // Comment! // Comment 2!"

    seq_comment = validate_sequence(raw_text)
    if seq_comment:
        seq, comment = seq_comment
        print(repr(seq))
    else:
        print("Sequence is invalid!")
