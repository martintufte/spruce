import re
import numpy as np
from typing import Union
from .permutations import (
    get_permutations,
    count_solved,
    corner_cycle,
    edge_cycle,
    SOLVED
)

PERMUTATIONS = get_permutations(3)


def is_valid_rubiks_cube_symbols(seq: str):
    """Check that a string only contains valid symbols."""

    return all(char in "RLFBUDMESrlfbudxyzw2' ()/\t\n" for char in seq)


def split_into_sequence_comment(raw_seq: str):
    """Split a sequence into moves and comment."""

    # Remove comments
    if "//" not in raw_seq:
        seq = raw_seq
        comment = ""
    else:
        seq = raw_seq.split("//")[0]
        comment = "//".join(raw_seq.split("//")[1:])

    return seq.strip(), comment.strip()


def format_whitespaces(seq: str):
    """Format whitespaces in a sequence."""

    # Add extra space before starting moves
    seq = re.sub(r"([RLFBUDMESxyz])", r" \1", seq)

    # Add space before and after parentheses
    seq = re.sub(r"(\()", r" \1", seq)
    seq = re.sub(r"(\))", r"\1 ", seq)

    # Remove extra spaces
    seq = re.sub(r"\s+", " ", seq)

    # Remove spaces before and after parentheses
    seq = re.sub(r"\s+\)", ")", seq)
    seq = re.sub(r"\(\s+", "(", seq)

    # Remove spaces before wide moves, apostrophes and double moves
    seq = re.sub(r"\s+w", "w", seq)
    seq = re.sub(r"\s+2", "2", seq)
    seq = re.sub(r"\s+'", "'", seq)

    return seq.strip()


def replace_old_wide_notation(sequence: str):
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
        sequence = sequence.replace(old, new)
    return sequence


def is_valid_rubiks_cube_moves(seq: str):
    """Check if a string is valid Rubik's Cube notation."""

    # Remove comments and parentheses
    seq, _ = split_into_sequence_comment(seq)
    seq = seq.replace("(", "").replace(")", "")

    # Check if the sequence has correct moves
    pattern = r"^[RLFBUD][w][2']?$|^[RLUDFBxyzMESrludfb][2']?$"

    return all(re.match(pattern, move) for move in seq.split())


def validate_sequence(raw_string: str) -> None | tuple[str, str]:
    """Validate a string for Rubiks Cube."""
    seq, comment = split_into_sequence_comment(raw_string)

    assert is_valid_rubiks_cube_symbols(seq), (
        "Invalid symbols in sequence!"
    )

    seq = replace_old_wide_notation(seq)
    seq = format_whitespaces(seq)

    assert is_valid_rubiks_cube_moves(seq), (
        "Invalid Rubik's Cube moves!"
    )

    return seq, comment


def split_sequence(sequence: str):
    """Split a sequence into inverse and normal moves."""

    inverse_moves = ""
    normal_moves = ""

    if "(" in sequence:
        idx = sequence.find("(")
        normal_moves = sequence[:idx].strip()
        inverse_moves = sequence[idx:].strip()
        return normal_moves, inverse_moves
    return sequence.strip(), ""


def debug_cube_state(cube_state):
    """Get a debug text for a scramble."""
    p = cube_state.get_permutation()

    text = "EO count: (F/B: ?, R/L: ?, U/D: ?)  \n"
    text += f"Blind trace: {corner_cycle(p)} {edge_cycle(p)}  \n"
    text += f"Number of solved pieces: {count_solved(p)}  \n"

    return text


def get_cube_permutation(sequence: str = "") -> np.ndarray:
    """Get a cube permutation."""

    perm = np.copy(SOLVED)

    for move in sequence.split():
        perm = perm[PERMUTATIONS[move]]

    return perm


def apply_moves(permutation, sequence):
    """Apply a sequence of moves to the permutation."""
    for move in sequence.strip().split():
        permutation = permutation[PERMUTATIONS[move]]

    return permutation


def count_length(sequence, count_rotations=False, metric="HTM"):
    """Count the length of a sequence."""

    sequence = sequence.replace("(", "").replace(")", "").strip()

    sum_rotations = sum(1 for char in sequence if char in "xyz")
    sum_slices = sum(1 for char in sequence if char in "MES")
    sum_double_moves = sum(1 for char in sequence if char in "2")
    sum_moves = len(sequence.split())

    if not count_rotations:
        sum_moves -= sum_rotations

    if metric == "HTM":
        return sum_moves + sum_slices
    elif metric == "STM":
        return sum_moves
    elif metric == "QTM":
        return sum_moves + sum_double_moves

    raise ValueError(f"Invalid metric: {metric}")


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


if __name__ == "__main__":

    raw_seq = " R2(\t x' \nU2b)L 'D w \t // Comment! // Comment 2!"

    seq_comment = validate_sequence(raw_seq)
    if seq_comment:
        seq, comment = seq_comment
        print(seq)
    else:
        print("Sequence is invalid!")
