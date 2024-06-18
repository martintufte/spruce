import numpy as np

from rubiks_cube.state.permutation import SOLVED_STATE
from rubiks_cube.state.permutation import create_permutations
from rubiks_cube.state.permutation.utils import inverse
from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.move.sequence import cleanup
from rubiks_cube.move import is_rotation


def get_state(
    sequence: MoveSequence,
    inverse_sequence: MoveSequence | None = None,
    starting_state: np.ndarray = SOLVED_STATE,
    orientate_after: bool = False,
) -> np.ndarray:
    """Get the cube state from a sequence of moves."""

    permutation_dict = create_permutations()
    state = starting_state.copy()

    if inverse_sequence is not None:
        inverse_state = get_state(
            starting_state=inverse(state),
            sequence=inverse_sequence,
            orientate_after=orientate_after,
        )
        state = inverse(inverse_state)

    for move in cleanup(sequence):
        if orientate_after and is_rotation(move):
            break
        state = state[permutation_dict[move]]

    return state
