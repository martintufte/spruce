import numpy as np

from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.move.generator import MoveGenerator

from rubiks_cube.state import get_rubiks_cube_state
from rubiks_cube.state.permutation import SOLVED_STATE
from rubiks_cube.state.permutation.utils import invert
from rubiks_cube.state.permutation import apply_moves_to_state
from rubiks_cube.state.tag.patterns import get_cubexes
from rubiks_cube.state.tag.patterns import CubePattern


all_actions = ["F", "B", "L", "R", "U", "D", "F'", "B'", "L'", "R'",
               "U'", "D'", "F2", "B2", "L2", "R2", "U2", "D2"]
axis = {
    "F": "fb",
    "B": "fb",
    "L": "lr",
    "R": "lr",
    "U": "ud",
    "D": "ud",
}
axis_actions = {
    "fb": ["F", "B", "F'", "B'", "F2", "B2"],
    "lr": ["L", "R", "L'", "R'", "L2", "R2"],
    "ud": ["U", "D", "U'", "D'", "U2", "D2"],
}


def get_actions(seq):
    if len(seq) == 0:
        return all_actions
    last_face = seq[-1][0]
    last_axis = axis[last_face]
    if len(seq) > 1:
        last_face2 = seq[-2][0]
        last_axis2 = axis[last_face2]
        if last_axis == last_axis2 and last_face != last_face2:
            return [
                action
                for action in all_actions
                if action not in axis_actions[last_axis]
            ]
    return [
        action
        for action in all_actions
        if not action.startswith(last_face)
    ]


def iter_scrambles(seq=[], max_depth=5):
    """ Generator for all scrambles """
    scrambles_current_depth = [seq]
    i = 0
    while i < max_depth:
        i += 1
        scrambles_next_depth = []
        for seq in scrambles_current_depth:
            for action in get_actions(seq):
                scrambles_next_depth.append(seq + [action])
                yield seq + [action]
        scrambles_current_depth = scrambles_next_depth


def optimal_solution(
    permutation: np.ndarray,
    pattern_state: np.ndarray = SOLVED_STATE,
    max_search_depth: int = 4
) -> MoveSequence | None:
    """Return the optimal solution for a scramble up to a certain depth.
    It uses a bidirectional search algorithm to find the optimal solution.

    This code is slow, but works.

    Args:
        sequence (MoveSequence): The sequence of moves to solve.
        max_search_depth (int, optional): Maximum search depth. Defaults to 4.

    Returns:
        MoveSequence | None: Return the optimal solution if found.
    """

    # Last searched permutations and all searched states on normal permutation
    last_searched_permutation_normal: dict = {
        str(permutation): (permutation, [])
    }
    all_searched_states_normal: dict = {
        str(pattern_state[permutation]): []
    }

    # Last searched permutations and all searched states on inverse permutation
    last_searched_permutation_inverse: dict = {
        str(SOLVED_STATE): (SOLVED_STATE, [])
    }
    all_searched_states_inverse: dict = {
        str(pattern_state): []
    }

    for i in range(max_search_depth):
        print("Depth: {}".format(i + 1))

        # Expand last searched states on normal permutation
        new_searched_states_normal: dict = {}
        for permutation, move_list in last_searched_permutation_normal.values():  # noqa: E501
            for move in get_actions(move_list):
                new_permutation = apply_moves_to_state(
                    permutation,
                    MoveSequence([move])
                )
                new_state_str = str(pattern_state[new_permutation])
                if new_state_str not in all_searched_states_normal:
                    new_move_list = move_list + [move]
                    new_searched_states_normal[new_state_str] = (
                        new_permutation, new_move_list
                    )

                    # Check if inverse permutation is already searched
                    new_permutation_inverse = invert(new_permutation)
                    new_state_inverse_str = str(new_permutation_inverse)
                    if new_state_inverse_str in all_searched_states_inverse:  # noqa: E501
                        return MoveSequence(
                            move_list +
                            [move] +
                            all_searched_states_inverse[
                                new_state_inverse_str
                            ][1])
        all_searched_states_normal.update(new_searched_states_normal)
        last_searched_permutation_normal = new_searched_states_normal

        # Expand last searched states on inverse permutation
        new_searched_states_inverse: dict = {}
        for permutation, move_list in last_searched_permutation_inverse.values():  # noqa: E501
            for move in get_actions(move_list):
                new_permutation = apply_moves_to_state(
                    permutation,
                    MoveSequence([move])
                )
                new_state_str = str(pattern_state[new_permutation])
                if new_state_str not in all_searched_states_inverse:
                    new_move_list = move_list + [move]
                    new_searched_states_inverse[new_state_str] = (
                        new_permutation, new_move_list,
                    )

                    # Check if inverse permutation is already searched
                    new_permutation_inverse = invert(new_permutation)
                    new_state_inverse_str = str(pattern_state[new_permutation_inverse])  # noqa: E501
                    if new_state_inverse_str in all_searched_states_normal:  # noqa: E501
                        return MoveSequence(
                            all_searched_states_normal[
                                new_state_inverse_str
                            ][1] + move_list + [move])
        all_searched_states_inverse.update(new_searched_states_inverse)
        last_searched_permutation_inverse = new_searched_states_inverse

    return None


def get_permutation_list(generator: MoveGenerator) -> list:
    """Get a list of permutations."""

    generator_helper = {
        "L": ["L", "L'", "L2"],
        "R": ["R", "R'", "R2"],
        "U": ["U", "U'", "U2"],
        "D": ["D", "D'", "D2"],
        "F": ["F", "F'", "F2"],
        "B": ["B", "B'", "B2"],
        "M": ["M", "M'", "M2"],
        "E": ["E", "E'", "E2"],
        "S": ["S", "S'", "S2"],
        "x": ["x", "x'", "x2"],
        "y": ["y", "y'", "y2"],
        "z": ["z", "z'", "z2"],
    }

    # Create a lsit of all permutations
    permutation_list = []
    for sequence in generator:
        if len(sequence) == 1:
            for move in generator_helper.get(sequence[0], sequence[0]):
                permutation = get_rubiks_cube_state(
                    MoveSequence(move),
                    orientate_after=True,
                )
                permutation_list.append(permutation)
    return permutation_list


def create_pattern_state_from_pattern(pattern: CubePattern) -> np.ndarray:
    """Create a goal state from a pattern using the mask and orientations."""

    # Create the goal state
    goal_state = SOLVED_STATE.copy()
    if pattern.mask is not None:
        goal_state[~pattern.mask] = max(goal_state) + 1
    for orientation in pattern.orientations:
        goal_state[orientation] = max(goal_state) + 1

    # Reindex the goal state
    indexes = sorted(list(set(list(goal_state))))
    for i, index in enumerate(indexes):
        goal_state[goal_state == index] = i

    return goal_state


def solve_step(
    sequence: MoveSequence,
    generator: MoveGenerator,
    tag: str,
    pattern_idx: int = 0,
    goal_permutation: np.ndarray | None = None,
    n_solutions: int = 1,  # not implemented
    min_length: int = 0,  # not implemented
    max_length: int = 8,  # not implemented
    can_invert_before: bool = False,  # not implemented
    can_invert_during: bool = False,  # not implemented
) -> list[MoveSequence | None]:
    """Solve a single step."""

    # Create a matrix over permutations
    # permutation_list = get_permutation_list(generator)

    # Initial permutation
    initial_permutation = get_rubiks_cube_state(sequence, orientate_after=True)

    # Update the initial state if a goal state is given
    if goal_permutation is None:
        goal_permutation = SOLVED_STATE
    else:
        initial_permutation = invert(goal_permutation)[initial_permutation]

    # Goal state for the step
    cubex = get_cubexes()
    if tag not in cubex:
        raise ValueError("Cannot find the tag. Will not solve the step.")
    pattern = cubex[tag].patterns[pattern_idx]

    # Retrieve the mask and the orientation
    pattern_state = create_pattern_state_from_pattern(pattern)
    print("Pattern:", inline_print_permutation(pattern_state))

    # Find an optimal solution
    optimal = optimal_solution(
        permutation=initial_permutation,
        pattern_state=pattern_state,
    )

    return [optimal]


def inline_print_permutation(permutation: np.ndarray) -> None:
    """Print the permutation in a readable format."""

    print("Permutation:")
    for i, face in zip(range(6), "UFRBLD"):
        print(f"{face}: [" + " ".join([str(permutation[j]).rjust(2) for j in range(i * 9, (i + 1) * 9)]) + "]")  # noqa: E501
    print()


if __name__ == "__main__":
    seq = MoveSequence("D2 R2 D' R2 F2 R2 D' F2 L2 U2 B L' R2 B2 D L2 B D' U")  # noqa: E501
    gen = MoveGenerator("<L, R, U, D, F, B>")

    print("Sequence:", seq)
    print("Generator:", gen)

    solution = solve_step(seq, gen, "cross", pattern_idx=4)

    print(solution)
