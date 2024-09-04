from rubiks_cube.configuration import CUBE_SIZE
from rubiks_cube.move import is_rotation
from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.move.sequence import cleanup
from rubiks_cube.move.sequence import decompose
from rubiks_cube.state.permutation import create_permutations
from rubiks_cube.state.permutation import get_identity_permutation
from rubiks_cube.state.permutation.utils import invert
from rubiks_cube.utils.types import CubeState


def get_rubiks_cube_state(
    sequence: MoveSequence,
    initial_state: CubeState | None = None,
    use_inverse: bool = True,
    orientate_after: bool = False,
    invert_after: bool = False,
    cube_size: int = CUBE_SIZE,
) -> CubeState:
    """Get the cube state from a sequence of moves.

    Args:
        sequence (MoveSequence): Rubiks cube move sequence.
        initial_state (CubeState, optional): Initial state of the cube.
            Defaults to SOLVED_STATE.
        orientate_after (bool, optional): Orientate to same orientation as the
            initial state. Defaults to False.
        use_inverse (bool, optional): Use the inverse part. Defaults to True.
        invert_state (bool, optional): Whether to invert. Defaults to False.
        cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.

    Returns:
        CubeState: The Rubiks cube state.
    """

    if initial_state is None:
        initial_state = get_identity_permutation(cube_size=cube_size)

    # Decompose the sequence
    normal_sequence, inverse_sequence = decompose(sequence)
    permutation_dict = create_permutations(cube_size=cube_size)
    state = initial_state.copy()

    # Apply moves on inverse
    if inverse_sequence and use_inverse:
        inverse_state = get_rubiks_cube_state(
            sequence=inverse_sequence,
            initial_state=invert(state),
            orientate_after=orientate_after,
            cube_size=cube_size,
        )
        state = invert(inverse_state)

    # Apply moves on normal
    for move in cleanup(normal_sequence, size=cube_size):
        if orientate_after and is_rotation(move):
            break
        state = state[permutation_dict[move]]

    if invert_after:
        state = invert(state)
    return state
