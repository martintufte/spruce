# About 20-50% faster execution time than the original code

import time
import numpy as np

from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.move.generator import MoveGenerator

from rubiks_cube.state import get_rubiks_cube_state
from rubiks_cube.state.permutation import SOLVED_STATE
from rubiks_cube.state.permutation.utils import invert
from rubiks_cube.state.tag.patterns import get_cubexes
from rubiks_cube.state.tag.patterns import CubePattern
from rubiks_cube.move.sequence import cleanup


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


def get_actions(generator: MoveGenerator) -> dict[str, np.ndarray]:
    """Get a list of permutations."""

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

    # Create a lsit of all permutations
    actions = {}
    for sequence in generator:
        for move in move_expander.get(sequence[0], [sequence[0]]):
            permutation = get_rubiks_cube_state(MoveSequence(move))
            actions[move] = permutation
    return actions


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
    generator: MoveGenerator = MoveGenerator("<L, R, U, D, F, B>"),
    step: str = "solved",
    goal_state: np.ndarray | None = None,
    max_search_depth: int = 10,
    n_solutions: int = 1,
    search_inverse: bool = False,
) -> list[MoveSequence]:
    """Solve a single step."""

    # Initial permutation
    initial_permutation = get_rubiks_cube_state(sequence)
    if goal_state is not None:
        initial_permutation = invert(goal_state)[initial_permutation]

    # Step to solve
    cubexes = get_cubexes()
    if step not in cubexes:
        raise ValueError("Cannot find the step. Will not solve the step.")

    # Action space with permutations to search
    actions = get_actions(generator)

    # Retrieve the matchable pattern
    cubex = cubexes[step].patterns[0]  # only uses the first pattern
    pattern = create_pattern_state_from_pattern(cubex)

    print("Pattern:", pattern)

    # Optimization: Remove idexes that are not part of the action space
    boolean_match = np.zeros_like(SOLVED_STATE, dtype=bool)
    for permutation in actions.values():
        boolean_match |= SOLVED_STATE != permutation
    initial_permutation = initial_permutation[boolean_match]
    pattern = pattern[boolean_match]
    for p in actions:
        actions[p] = actions[p][boolean_match]
    for new_index, index in enumerate(np.where(boolean_match)[0]):
        initial_permutation[initial_permutation == index] = new_index
        for p in actions:
            actions[p][actions[p] == index] = new_index

    if search_inverse:
        initial_permutation = invert(initial_permutation)

    solutions = bidirectional_solver(
        initial_permutation=initial_permutation,
        actions=actions,
        pattern=pattern,
        max_search_depth=max_search_depth,
        n_solutions=n_solutions,
    )

    if search_inverse and solutions is not None:
        solutions = {
            "(" + solution + ")"
            for solution in solutions
        }

    if solutions is not None:
        return sorted([MoveSequence(sol) for sol in solutions], key=len)
    return []


if __name__ == "__main__":
    # sequence = MoveSequence("D2 R2 D' R2 F2 R2 D' F2")
    # generator = MoveGenerator("<L, R, U, D, F, B>")

    sequence = MoveSequence("R' U' F D2 L U2 F2 D2 L2 F2 L F2 R' U2 R' U' R' F' L D2 F' U' L' U' R' U' F")  # noqa: E501
    generator = MoveGenerator("<L, R, F, B, U, D>")
    step = "eo-lr"
    max_search_depth = 8
    n_solutions = 20
    search_inverse = True

    print("Sequence:", sequence)
    print("Generator:", generator)
    print("Step:", step)

    t = time.time()
    solutions = solve_step(
        sequence=sequence,
        generator=generator,
        step=step,
        max_search_depth=max_search_depth,
        n_solutions=n_solutions,
        search_inverse=search_inverse,
    )

    print("Time:", time.time() - t)
    print("Solutions:")
    for solution in solutions if solutions is not None else []:
        print(solution)
