from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.move.generator import MoveGenerator

from rubiks_cube.state import get_rubiks_cube_state
from rubiks_cube.state.permutation import SOLVED_STATE
from rubiks_cube.state.permutation.utils import invert
from rubiks_cube.state.permutation import apply_moves_to_state


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
    sequence: MoveSequence,
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

    permutation = get_rubiks_cube_state(sequence, orientate_after=True)
    solved = SOLVED_STATE

    last_searched_states_normal: dict = {
        str(permutation): (permutation, [])
    }
    all_searched_states_normal: dict = {
        str(permutation): []
    }
    last_searched_states_inverse: dict = {
        str(solved): (solved, [])
    }
    all_searched_states_inverse: dict = {
        str(solved): []
    }

    for i in range(max_search_depth):
        print("Depth: {}".format(i + 1))

        # Expand last searched states on normal permutation
        new_searched_states_normal: dict = {}
        for permutation, move_list in last_searched_states_normal.values():
            for move in get_actions(move_list):
                new_permutation = apply_moves_to_state(
                    permutation,
                    MoveSequence([move])
                )
                new_permutation_str = str(new_permutation)
                if new_permutation_str not in all_searched_states_normal:
                    new_move_list = move_list + [move]
                    new_searched_states_normal[new_permutation_str] = (
                        new_permutation, new_move_list
                    )

                    # Check if inverse permutation is already searched
                    new_permutation_inverse = invert(new_permutation)
                    new_permutation_inverse_str = str(new_permutation_inverse)
                    if new_permutation_inverse_str in all_searched_states_inverse:  # noqa: E501
                        return MoveSequence(
                            move_list +
                            [move] +
                            all_searched_states_inverse[
                                new_permutation_inverse_str
                            ][1])
        all_searched_states_normal.update(new_searched_states_normal)
        last_searched_states_normal = new_searched_states_normal

        # Expand last searched states on inverse permutation
        new_searched_states_inverse: dict = {}
        for permutation, move_list in last_searched_states_inverse.values():
            for move in get_actions(move_list):
                new_permutation = apply_moves_to_state(
                    permutation,
                    MoveSequence([move])
                )
                new_permutation_str = str(new_permutation)
                if new_permutation_str not in all_searched_states_inverse:
                    new_move_list = move_list + [move]
                    new_searched_states_inverse[new_permutation_str] = (
                        new_permutation,
                        new_move_list,
                    )

                    # Check if inverse permutation is already searched
                    new_permutation_inverse = invert(new_permutation)
                    new_permutation_inverse_str = str(new_permutation_inverse)
                    if new_permutation_inverse_str in all_searched_states_normal:  # noqa: E501
                        return MoveSequence(
                            all_searched_states_normal[
                                new_permutation_inverse_str
                            ][1] + move_list + [move])
        all_searched_states_inverse.update(new_searched_states_inverse)
        last_searched_states_inverse = new_searched_states_inverse

    return None


def solve_single_step(
    sequence: MoveSequence,
    generator: MoveGenerator,
    tag: str,
    n_solutions: int = 1,
    min_length: int = 0,
    max_length: int = 8,
    can_invert_before: bool = False,
    can_invert_during: bool = False,
) -> list[MoveSequence]:
    """Solve a single step."""

    # PERMUTATIONS = create_permutations()

    # Get the initial state
    # initial_state = get_rubiks_cube_state(sequence, orientate_after=True)

    # Get the goal state
    # goal_state = SOLVED_STATE

    optimal = optimal_solution(sequence)

    if optimal is not None:
        return [optimal]
    else:
        return [MoveSequence()]


if __name__ == "__main__":
    seq = MoveSequence("M2 E2 S2 F'")
    gen = MoveGenerator("<L, R, U, D, F, B>")
    print(solve_single_step(seq, gen, "test"))
