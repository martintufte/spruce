import time
import numpy as np

from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.move.generator import MoveGenerator

from rubiks_cube.configuration import CUBE_SIZE
from rubiks_cube.state import get_rubiks_cube_state
from rubiks_cube.state.permutation import get_solved_state
from rubiks_cube.state.permutation.utils import invert
from rubiks_cube.state.tag.patterns import get_cubexes
from rubiks_cube.state.tag.patterns import CubePattern
from rubiks_cube.move.sequence import cleanup
from rubiks_cube.state.permutation import get_piece_mask
from rubiks_cube.state.permutation import unorientate_mask
from rubiks_cube.utils.enumerations import Piece


def bidirectional_solver(
    initial_permutation: np.ndarray,
    actions: dict[str, np.ndarray],
    pattern: np.ndarray,
    max_search_depth: int = 10,
    n_solutions: int = 1,
) -> set[str] | None:
    """Bidirectional solver for the Rubik's cube.
    It uses a breadth-first search from both states to find the shortest path
    between two states and returns the optimal solution.

    Args:
        initial_permutation (np.ndarray): The initial permutation.
        actions (dict[str, np.ndarray]): A dictionary of actions and
            permutations.
        pattern (np.ndarray, optional): The pattern that must match.
            Defaults to SOLVED_STATE.
        max_search_depth (int, optional): The maximum depth. Defaults to 10.
        n_solutions (int, optional): The number of solutions to find.
            Defaults to 1.
        search_inverse (bool, optional): Search the inverse permutation.

    Returns:
        MoveSequence | None: The first optimal solution found.
    """
    def encode(permutation: np.ndarray) -> str:
        return str(pattern[permutation])

    initial_str = encode(initial_permutation)
    last_states_normal: dict[str, tuple[np.ndarray, list]] = {
        initial_str: (initial_permutation, [])
    }
    searched_states_normal: dict = {initial_str: (initial_permutation, [])}

    # Last searched permutations and all searched states on inverse permutation
    identity = np.arange(len(initial_permutation))
    solved_str = encode(identity)
    last_states_inverse: dict[str, tuple[np.ndarray, list]] = {
        solved_str: (identity, [])
    }
    searched_states_inverse: dict = {solved_str: (identity, [])}

    solutions = set()

    # Check if the initial state is solved
    print("Search depth: 0")
    if initial_str in searched_states_inverse:
        print("Found solution")
        return set("")

    for i in range(max_search_depth // 2):
        # Expand last searched states on normal permutation
        print(f"Search depth: {2*i + 1}")
        new_searched_states_normal: dict = {}
        for permutation, move_list in last_states_normal.values():
            for move, action in actions.items():
                new_permutation = permutation[action]
                new_state_str = encode(new_permutation)
                if new_state_str not in searched_states_normal:
                    new_move_list = move_list + [move]
                    new_searched_states_normal[new_state_str] = (new_permutation, new_move_list)  # noqa: E501

                    # Check if inverse permutation is searched
                    new_inverse_str = encode(new_permutation)
                    if new_inverse_str in last_states_inverse:
                        solution = MoveSequence(new_move_list) + ~MoveSequence(last_states_inverse[new_inverse_str][1])  # noqa: E501
                        solution_str = str(cleanup(solution))
                        if solution_str not in solutions:
                            solutions.add(solution_str)
                            print(f"Found solution ({len(solutions)}/{n_solutions})")  # noqa: E501
                        if len(solutions) >= n_solutions:
                            return solutions

        searched_states_normal.update(new_searched_states_normal)
        last_states_normal = new_searched_states_normal

        # Expand last searched states on inverse permutation
        print(f"Search depth: {2*i + 2}")
        new_searched_states_inverse: dict = {}
        for permutation, move_list in last_states_inverse.values():
            for move, action in actions.items():
                new_permutation = permutation[action]
                new_state_str = encode(new_permutation)
                if new_state_str not in searched_states_inverse:
                    new_move_list = move_list + [move]
                    new_searched_states_inverse[new_state_str] = (new_permutation, new_move_list)  # noqa: E501

                    # Check if inverse permutation is searched
                    new_inverse_str = encode(invert(new_permutation))
                    if new_inverse_str in last_states_normal:
                        solution = MoveSequence(last_states_normal[new_inverse_str][1] + new_move_list)  # noqa: E501
                        solution_str = str(cleanup(solution))
                        if solution_str not in solutions:
                            solutions.add(solution_str)
                            print(f"Found solution ({len(solutions)}/{n_solutions})")  # noqa: E501
                        if len(solutions) >= n_solutions:
                            return solutions

        searched_states_inverse.update(new_searched_states_inverse)
        last_states_inverse = new_searched_states_inverse

    return solutions


def get_action_space(generator: MoveGenerator, cube_size: int) -> dict[str, np.ndarray]:  # noqa: E501
    """Get a list of actions."""

    # TODO: Generalize this for all cube sizes
    move_expander = {
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
    move_expander.update({
        "Lw": ["Lw", "Lw'", "Lw2"],
        "Rw": ["Rw", "Rw'", "Rw2"],
        "Uw": ["Uw", "Uw'", "Uw2"],
        "Dw": ["Dw", "Dw'", "Dw2"],
        "Fw": ["Fw", "Fw'", "Fw2"],
        "Bw": ["Bw", "Bw'", "Bw2"],
    })

    # Create a lsit of all permutations
    actions = {}
    for sequence in generator:
        for move in move_expander.get(sequence[0], [sequence[0]]):
            permutation = get_rubiks_cube_state(MoveSequence(move), cube_size=cube_size)  # noqa: E501
            actions[move] = permutation
    return actions


def create_pattern_state_from_pattern(pattern: CubePattern) -> np.ndarray:
    """Create a goal state from a pattern using the mask and orientations."""

    # Create the goal state
    goal_state = get_solved_state(cube_size=pattern.size)
    if pattern.mask is not None:
        goal_state[~pattern.mask] = max(goal_state) + 1
    for orientation in pattern.orientations:
        goal_state[orientation] = max(goal_state) + 1

    # Reindex the goal state
    indexes = sorted(list(set(list(goal_state))))
    for i, index in enumerate(indexes):
        goal_state[goal_state == index] = i

    return goal_state


# TODO: Fix a bug!
def optimize_indecies(
    initial_permutation: np.ndarray,
    actions: dict[str, np.ndarray],
    pattern: np.ndarray,
    cube_size: int = CUBE_SIZE,
) -> tuple[np.ndarray, dict[str, np.ndarray], np.ndarray]:
    """Optimize the permutations and action space.

    1. Identify indecies that are not affected by the action space.
    2. Identify conserved orientations of corners and edges.
    3. Reindex the permutations and action space.

    Args:
        initial_permutation (np.ndarray): Initial permutation.
        actions (dict[str, np.ndarray]): Action space.
        pattern (np.ndarray): Pattern.

    Returns:
        tuple[np.ndarray, dict[str, np.ndarray], np.ndarray]: _description_
    """
    boolean_mask = np.zeros_like(initial_permutation, dtype=bool)

    # Identify the indexes that are not affected by the action space
    identity = np.arange(len(initial_permutation))
    for permutation in actions.values():
        boolean_mask |= identity != permutation

    # Identify conserved orientations of corners and edges
    for piece in [Piece.corner, Piece.edge]:
        piece_mask = get_piece_mask(piece, cube_size=cube_size)
        union_mask = boolean_mask & piece_mask

        while np.any(union_mask):
            # Initialize a mask for the first piece in the union mask
            mask = np.zeros_like(identity, dtype=bool)
            mask[np.argmax(union_mask)] = True

            # Find all the other indecies that the piece can reach
            while True:
                new_mask = mask.copy()
                for permutation in actions.values():
                    new_mask |= mask[permutation]
                # No new indecies found, break the loop
                if np.all(mask == new_mask):
                    break
                mask = new_mask

            # No orientation found for the piece, cannot remove the indexes
            if np.all(mask == union_mask):
                break

            unorientated_mask = unorientate_mask(mask, cube_size=cube_size)
            union_mask &= ~unorientated_mask
            boolean_mask[unorientated_mask ^ mask] = False

    # Remove the indexes that are not affected by the action space
    initial_permutation = initial_permutation[boolean_mask]
    pattern = pattern[boolean_mask]
    for action in actions:
        actions[action] = actions[action][boolean_mask]

    # Reindex the permutations and action space
    for new_index, index in enumerate(np.where(boolean_mask)[0]):
        initial_permutation[initial_permutation == index] = new_index
        for p in actions:
            actions[p][actions[p] == index] = new_index

    print(f"Optimizer reduced from {len(boolean_mask)} to {sum(boolean_mask)} indecies.")  # noqa: E501

    return initial_permutation, actions, pattern


def solve_step(
    sequence: MoveSequence,
    generator: MoveGenerator = MoveGenerator("<L, R, U, D, F, B>"),
    step: str = "solved",
    goal_state: np.ndarray | None = None,
    max_search_depth: int = 10,
    n_solutions: int = 1,
    search_inverse: bool = False,
    cube_size: int = CUBE_SIZE,
) -> list[MoveSequence]:
    """Solve a single step."""

    # Set the initial permutation for the search
    initial_permutation = get_rubiks_cube_state(sequence, cube_size=cube_size)
    if goal_state is not None:
        initial_permutation = invert(goal_state)[initial_permutation]
    if search_inverse:
        initial_permutation = invert(initial_permutation)

    # Get the action space from the generator
    actions = get_action_space(generator, cube_size)

    # Create matchable pattern
    if cube_size == 3:
        cubexes = get_cubexes(cube_size=cube_size)
        if step not in cubexes:
            raise ValueError("Cannot find the step. Will not solve the step.")
        cubex = cubexes[step].patterns[0]
        pattern = create_pattern_state_from_pattern(cubex)
    else:
        pattern = get_solved_state(cube_size=cube_size)

    # Optimize the indecies in the permutations and pattern
    initial_permutation, actions, pattern = optimize_indecies(
        initial_permutation=initial_permutation,
        actions=actions,
        pattern=pattern,
        cube_size=cube_size,
    )

    # Solve the step using a bidirectional search
    t = time.time()
    solutions = bidirectional_solver(
        initial_permutation=initial_permutation,
        actions=actions,
        pattern=pattern,
        max_search_depth=max_search_depth,
        n_solutions=n_solutions,
    )
    print("Walltime:", time.time() - t)

    if search_inverse and solutions is not None:
        solutions = {
            "(" + solution + ")"
            for solution in solutions
        }

    if solutions is not None:
        return sorted([MoveSequence(sol) for sol in solutions], key=len)
    return []


def main() -> None:
    """Example of solving a step with a generator on a 3x3 cube.
    """
    cube_size = 3
    scr = MoveSequence("R' U' F U L' B' R D B2 R' B L F' L2 U' R2 D' F2 R2 U2 F2 L2 B2 D2 R' U' F")  # noqa: E501
    eo = MoveSequence("(R' U' B' F)")
    sequence = scr + eo
    generator = MoveGenerator("<L, R, F2, B2, U2, D2>")
    step = "dr-lr"
    max_search_depth = 10
    n_solutions = 1
    search_inverse = False

    print("Sequence:", sequence)
    print("Generator:", generator, "\tStep:", step)

    solutions = solve_step(
        sequence=sequence,
        generator=generator,
        step=step,
        max_search_depth=max_search_depth,
        n_solutions=n_solutions,
        search_inverse=search_inverse,
        cube_size=cube_size,
    )

    print("Solutions:")
    for solution in solutions if solutions is not None else []:
        print(solution)


if __name__ == "__main__":
    main()
