import numpy as np

from rubiks_cube.state.permutation import SOLVED_STATE
from rubiks_cube.state.permutation import create_permutations
from rubiks_cube.state.permutation.utils import invert
from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.move.sequence import cleanup
from rubiks_cube.move.sequence import decompose
from rubiks_cube.move import is_rotation


def get_state(
    sequence: MoveSequence,
    initial_state: np.ndarray = SOLVED_STATE,
    orientate_after: bool = False,
    pre_moves: bool = True,
) -> np.ndarray:
    """Get the cube state from a sequence of moves."""

    normal_sequence, inverse_sequence = decompose(sequence)
    permutation_dict = create_permutations()
    state = initial_state.copy()

    if inverse_sequence and pre_moves:
        inverse_state = get_state(
            sequence=inverse_sequence,
            initial_state=invert(state),
            orientate_after=orientate_after,
        )
        state = invert(inverse_state)

    for move in cleanup(normal_sequence):
        if orientate_after and is_rotation(move):
            break
        state = state[permutation_dict[move]]

    return state
