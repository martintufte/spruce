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


def is_valid(sequence: str):
    """Check if a sequence is WCA valid."""

    sequence = sequence.split("//")[0].strip()
    legal_characters = "UDFBLRudfblrMESxyzw2' ()"

    if len(sequence) == 0:
        return False
    elif any(ch not in legal_characters for ch in sequence):
        return False
    return True


def format_sequence(sequence: str):
    """Change the format of a sequence to be valid."""

    sequence = sequence.split("//")[0].strip()

    # Replace small letters with correct moves
    sequence = sequence.replace("u", "Uw")
    sequence = sequence.replace("d", "Dw")
    sequence = sequence.replace("f", "Fw")
    sequence = sequence.replace("b", "Bw")
    sequence = sequence.replace("l", "Lw")
    sequence = sequence.replace("r", "Rw")

    return sequence


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
