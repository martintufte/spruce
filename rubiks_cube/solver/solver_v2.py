# About 20-50% faster execution time than the original code

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


def get_actions(generator: MoveGenerator, cube_size: int) -> dict[str, np.ndarray]:  # noqa: E501
    """Get a list of permutations."""

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

    # Initial permutation
    initial_permutation = get_rubiks_cube_state(sequence, cube_size=cube_size)
    if goal_state is not None:
        initial_permutation = invert(goal_state)[initial_permutation]

    # Retrieve the matchable pattern (only for 3x3 cube)
    if cube_size == 3:
        cubexes = get_cubexes(cube_size=cube_size)
        if step not in cubexes:
            raise ValueError("Cannot find the step. Will not solve the step.")
        cubex = cubexes[step].patterns[0]  # only uses the first pattern
        pattern = create_pattern_state_from_pattern(cubex)
    else:
        pattern = get_solved_state(cube_size=cube_size)

    # Print pattern
    print("Pattern:", pattern)

    # Action space with permutations to search
    actions = get_actions(generator, cube_size)

    # Optimization: Remove idexes that are not part of the action space
    boolean_match = np.zeros_like(initial_permutation, dtype=bool)
    solved_state = get_solved_state(cube_size=cube_size)
    for permutation in actions.values():
        boolean_match |= solved_state != permutation
    initial_permutation = initial_permutation[boolean_match]
    pattern = pattern[boolean_match]
    for p in actions:
        actions[p] = actions[p][boolean_match]
    for new_index, index in enumerate(np.where(boolean_match)[0]):
        initial_permutation[initial_permutation == index] = new_index
        for p in actions:
            actions[p][actions[p] == index] = new_index
    print(f"Info: Removed {sum(boolean_match == 0)} of {len(boolean_match)} indexes!")  # noqa: E501

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


def main_example_2() -> None:
    """Example of solving a 2x2 cube.
    """
    cube_size = 2
    sequence = MoveSequence("R2 F' U' R' F' U' F2 R U'")  # noqa: E501
    generator = MoveGenerator("<R, U, F>")
    step = "solved"
    max_search_depth = 12
    n_solutions = 1
    search_inverse = False

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
        cube_size=cube_size,
    )

    print("Time:", time.time() - t)
    print("Solutions:")
    for solution in solutions if solutions is not None else []:
        print(solution)


def main_example_3() -> None:
    """Example of solving a step with a generator on a 3x3 cube.
    """
    cube_size = 3
    sequence = MoveSequence("D2 B2 U2 D B2 U L2 D' U2")
    generator = MoveGenerator("<U, D, F2, B2, L2, R2>")
    step = "solved"
    max_search_depth = 14
    n_solutions = 1
    search_inverse = False

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
        cube_size=cube_size,
    )

    print("Time:", time.time() - t)
    print("Solutions:")
    for solution in solutions if solutions is not None else []:
        print(solution)


def main_example_4() -> None:
    """Example of solving a step with a generator on a 4x4 cube."""
    cube_size = 4
    sequence = MoveSequence("Rw U2 x Rw U2 Rw U2 Rw' U2 Lw U2 Rw' U2 Rw U2 Rw' U2 Rw'")  # noqa: E501
    generator = MoveGenerator("<U2, Lw, Rw>")
    step = "solved"
    max_search_depth = 18
    n_solutions = 1
    search_inverse = False

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
        cube_size=cube_size,
    )

    print("Time:", time.time() - t)
    print("Solutions:")
    for solution in solutions if solutions is not None else []:
        print(solution)


if __name__ == "__main__":
    # main_example_2()
    # main_example_3()
    main_example_4()
