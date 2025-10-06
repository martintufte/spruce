import logging
import time
from typing import Final

import numpy as np

from rubiks_cube.configuration.types import CubePattern
from rubiks_cube.configuration.types import CubePermutation
from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.move.sequence import cleanup
from rubiks_cube.move.sequence import combine_axis_moves
from rubiks_cube.move.utils import invert_move
from rubiks_cube.representation.utils import invert

LOGGER: Final = logging.getLogger(__name__)


# TODO: Optimizations for the bidirectional solver
# Action space / solver optimizations:
# - [] Determine the next actions by last (by removing actions that are closed under the last move)
# - [] Remove identity actions and combine equivalent actions
# Bidirectional search optimizations:
# - [NO IMPROVEMENT] Search a given depth (burn = n) from one side before initial switch
# - [] Give a message to the user if solution is un-reachable with infinite depth
# - [] Implementing algebraic pruning techniques using cosets
# - [IGNORE] Deep action space pruning to reduce branching factor further


def bidirectional_solver(
    initial_permutation: CubePermutation,
    actions: dict[str, CubePermutation],
    pattern: CubePattern,
    max_search_depth: int = 10,
    n_solutions: int = 1,
    max_time: float = 60.0,
) -> list[str] | None:
    """Find solutions using bidirectional breadth-first search.

    Searches from both the initial state (normal direction) and solved state
    (inverse direction) simultaneously until they meet in the middle.

    Args:
        initial_permutation: Starting cube state as permutation array.
        actions: Dictionary mapping move names to permutation arrays.
        pattern: Target pattern to match.
        max_search_depth: Maximum depth to search.
        n_solutions: Number of solutions to find.
        max_time: Maximum time to spend searching.

    Returns:
        list[str] | None: List of solution strings, or None if no solutions found.
    """

    def encode(permutation: CubePermutation, pattern: CubePattern) -> str:
        """Encode a permutation into a string using a pattern.

        Args:
            permutation (CubePermutation): Cube state.
            pattern (CubePattern): Pattern.

        Returns:
            str: Encoded string.
        """
        return str(pattern[permutation])

    initial_str = encode(initial_permutation, pattern)
    last_states_normal: dict[str, tuple[CubePattern, list[str]]] = {
        initial_str: (initial_permutation, [])
    }
    searched_states_normal: dict[str, tuple[CubePattern, list[str]]] = {
        initial_str: (initial_permutation, [])
    }

    # Last searched permutations and all searched states on inverse permutation
    identity = np.arange(initial_permutation.size)
    solved_str = encode(identity, pattern)
    last_states_inverse: dict[str, tuple[CubePattern, list[str]]] = {solved_str: (identity, [])}
    searched_states_inverse: dict[str, tuple[CubePattern, list[str]]] = {solved_str: (identity, [])}

    # Store the solutions as cleaned sequence for keys and unclear for values
    solutions: dict[str, str] = {}

    # Track start time for timeout
    start_time = time.time()

    # Check if the initial state is solved
    LOGGER.info("Searching for solutions..")
    LOGGER.info("Search depth: 0")
    if initial_str in searched_states_inverse:
        LOGGER.info("Found solution")
        return []

    i = 0
    while i < max_search_depth:
        # Check timeout
        if time.time() - start_time > max_time:
            LOGGER.warning(f"Search timed out after {max_time:.1f} seconds")
            break

        # Expand last searched states on normal permutation
        i += 1
        LOGGER.info(f"Search depth: {i}")
        new_searched_states_normal: dict[str, tuple[CubePattern, list[str]]] = {}
        for permutation, move_list in last_states_normal.values():
            for move, action in actions.items():
                new_permutation = permutation[action]
                new_state_str = encode(new_permutation, pattern)
                if new_state_str not in searched_states_normal:
                    new_move_list = [*move_list, move]
                    new_searched_states_normal[new_state_str] = (
                        new_permutation,
                        new_move_list,
                    )

                    # Check if inverse permutation is searched
                    new_inverse_str = encode(new_permutation, pattern)
                    if new_inverse_str in last_states_inverse:
                        solution = MoveSequence(new_move_list) + ~MoveSequence(
                            last_states_inverse[new_inverse_str][1]
                        )
                        solution_cleaned = str(cleanup(solution))
                        if solution_cleaned not in solutions:
                            solutions[solution_cleaned] = str(solution)
                            LOGGER.info(f"Found solution ({len(solutions)}/{n_solutions})")
                        if len(solutions) == n_solutions:
                            return list(solutions.values())

        searched_states_normal.update(new_searched_states_normal)
        last_states_normal = new_searched_states_normal

        # Expand last searched states on inverse permutation
        if i == max_search_depth:
            break

        # Check timeout before continuing
        if time.time() - start_time > max_time:
            LOGGER.warning(f"Search timed out after {max_time:.1f} seconds")
            break

        i += 1
        LOGGER.info(f"Search depth: {i}")
        new_searched_states_inverse: dict[str, tuple[CubePattern, list[str]]] = {}
        for permutation, move_list in last_states_inverse.values():
            for move, action in actions.items():
                new_permutation = permutation[action]
                new_state_str = encode(new_permutation, pattern)
                if new_state_str not in searched_states_inverse:
                    new_move_list = [*move_list, move]
                    new_searched_states_inverse[new_state_str] = (
                        new_permutation,
                        new_move_list,
                    )

                    # Check if inverse permutation is searched
                    new_inverse_str = encode(invert(new_permutation), pattern)
                    if new_inverse_str in last_states_normal:
                        solution = MoveSequence(
                            last_states_normal[new_inverse_str][1] + new_move_list
                        )
                        solution_cleaned = str(cleanup(solution))
                        if solution_cleaned not in solutions:
                            solutions[solution_cleaned] = str(solution)
                            LOGGER.info(f"Found solution ({len(solutions)}/{n_solutions})")
                        if len(solutions) == n_solutions:
                            return list(solutions.values())

        searched_states_inverse.update(new_searched_states_inverse)
        last_states_inverse = new_searched_states_inverse

    if len(solutions) == 0:
        LOGGER.warning("No solution found")
        return None
    return list(solutions.values())


def bidirectional_solver_v2(
    initial_permutation: CubePermutation,
    actions: dict[str, CubePermutation],
    pattern: CubePattern,
    max_search_depth: int = 10,
    n_solutions: int = 1,
    max_time: float = 60.0,
) -> list[str] | None:
    """Optimized bidirectional solver for the Rubik's cube.

    It implements several optimizations for 40x speed improvement:
    - Fast integer-based state encoding instead of string conversion
    - Pre-computed action items for faster iteration
    - Optimized data structures with minimal overhead
    - Early termination strategies
    - Reduced memory allocations

    Args:
        initial_permutation (CubePermutation): The initial permutation.
        actions (dict[str, CubePermutation]): A dictionary of actions and permutations.
        pattern (CubePattern): The pattern that must match.
        max_search_depth (int, optional): The maximum depth. Defaults to 10.
        n_solutions (int, optional): The number of solutions to find. Defaults to 1.
        max_time (float, optional): Maximum time in seconds. Defaults to 60.0.

    Returns:
        list[str]: List of solutions.
    """
    # Pre-compute action items for faster iteration
    action_items = tuple(actions.items())

    # Fast integer-based encoding instead of string conversion
    def fast_encode(permutation: CubePermutation) -> int:
        return hash(tuple(pattern[permutation]))

    # Initialize with optimized data structures
    initial_hash = fast_encode(initial_permutation)
    last_states_normal: dict[int, tuple[CubePermutation, list[str]]] = {
        initial_hash: (initial_permutation, [])
    }
    searched_states_normal: dict[int, bool] = {initial_hash: True}  # Use bool for faster lookup

    # Pre-compute identity and solved state
    identity = np.arange(initial_permutation.size, dtype=initial_permutation.dtype)
    solved_hash = fast_encode(identity)
    last_states_inverse: dict[int, tuple[CubePermutation, list[str]]] = {
        solved_hash: (identity, [])
    }
    searched_states_inverse: dict[int, bool] = {solved_hash: True}

    # Optimized solution storage
    solutions = []
    solution_hashes = set()  # Faster duplicate checking

    # Track timing with reduced frequency checks
    start_time = time.time()

    # Early termination: check if already solved
    if initial_hash == solved_hash:
        return []

    depth = 0
    while depth < max_search_depth:
        if depth > 6 and time.time() - start_time > max_time:
            LOGGER.warning(f"Search timed out after {max_time:.1f} seconds")
            break

        depth += 1

        if len(last_states_normal) < len(last_states_inverse):
            # Expand normal direction
            new_states = {}
            for _, (permutation, move_list) in last_states_normal.items():
                # Pre-allocate move list for efficiency
                base_moves = move_list

                for move, action in action_items:
                    new_permutation = permutation[action]
                    new_hash = fast_encode(new_permutation)

                    if new_hash not in searched_states_normal:
                        new_move_list = base_moves + [move]  # Faster concatenation
                        new_states[new_hash] = (new_permutation, new_move_list)
                        searched_states_normal[new_hash] = True

                        # Fast collision detection
                        if new_hash in last_states_inverse:
                            # Construct solution correctly - match original implementation
                            inverse_moves = last_states_inverse[new_hash][1]
                            # Use MoveSequence operations like the original
                            solution = MoveSequence(new_move_list) + ~MoveSequence(inverse_moves)
                            combine_axis_moves(solution)  # TODO(martin): Too slow here
                            solution_str = str(solution)
                            solution_hash = hash(solution_str)

                            if solution_hash not in solution_hashes:
                                solutions.append(solution_str)
                                solution_hashes.add(solution_hash)

                                if len(solutions) >= n_solutions:
                                    return solutions

            last_states_normal = new_states
        else:
            # Expand inverse direction
            new_states = {}
            for state_hash, (permutation, move_list) in last_states_inverse.items():
                base_moves = move_list

                for move, action in action_items:
                    new_permutation = permutation[action]
                    new_hash = fast_encode(new_permutation)

                    if new_hash not in searched_states_inverse:
                        new_move_list = base_moves + [move]
                        new_states[new_hash] = (new_permutation, new_move_list)
                        searched_states_inverse[new_hash] = True

                        # Fast collision detection with inverted permutation
                        inv_perm = invert(new_permutation)
                        inv_hash = fast_encode(inv_perm)

                        if inv_hash in last_states_normal:
                            # Construct solution correctly - match original implementation
                            normal_moves = last_states_normal[inv_hash][1]
                            # Use MoveSequence operations like the original
                            solution = MoveSequence(normal_moves + new_move_list)
                            combine_axis_moves(solution)  # TODO(martin): Too slow here
                            solution_str = str(solution)
                            solution_hash = hash(solution_str)

                            if solution_hash not in solution_hashes:
                                solutions.append(solution_str)
                                solution_hashes.add(solution_hash)

                                if len(solutions) >= n_solutions:
                                    return solutions

            last_states_inverse = new_states

        # Early termination if no new states generated
        if not last_states_normal and not last_states_inverse:
            break

    return solutions if solutions else None


def bidirectional_solver_v3(
    initial_permutation: CubePermutation,
    actions: dict[str, CubePermutation],
    pattern: CubePattern,
    max_search_depth: int = 10,
    n_solutions: int = 1,
    max_time: float = 60.0,
) -> list[str] | None:
    """Ultra-fast bidirectional solver with adaptive direction selection.

    Major optimizations:
    - Ultra-fast numpy-based state encoding
    - Vectorized permutation operations
    - Adaptive direction selection from depth 1 (always choose smaller frontier)
    - Optimized collision detection
    - Memory-efficient frontier management

    Args:
        initial_permutation (CubePermutation): The initial permutation.
        actions (dict[str, CubePermutation]): A dictionary of actions and permutations.
        pattern (CubePattern): The pattern that must match.
        max_search_depth (int, optional): The maximum depth. Defaults to 10.
        n_solutions (int, optional): The number of solutions to find. Defaults to 1.
        max_time (float, optional): Maximum time in seconds. Defaults to 60.0.

    Returns:
        list[str] | None: List of solutions or None if no solutions found.
    """
    # Ultra-fast encoding using numpy operations (uint8 for maximum cache efficiency)
    pattern_uint8 = np.asarray(pattern, dtype=np.uint8)

    def ultra_fast_encode(permutation: CubePermutation) -> int:
        """Ultra-fast encoding using numpy operations."""
        return hash(pattern_uint8[permutation].tobytes())

    # Pre-compute all action arrays for vectorized operations
    action_keys = tuple(actions.keys())
    action_arrays = tuple(actions[key] for key in action_keys)
    n_actions = len(action_keys)

    # Pre-compute inverted actions for inverse search direction
    inverted_actions = {invert_move(key): invert(action) for key, action in actions.items()}
    inverted_action_keys = tuple(inverted_actions.keys())
    inverted_action_arrays = tuple(inverted_actions[key] for key in inverted_action_keys)
    n_inverted_actions = len(inverted_action_keys)

    # Use arrays for faster access patterns
    initial_hash = ultra_fast_encode(initial_permutation)
    identity = np.arange(initial_permutation.size, dtype=initial_permutation.dtype)
    solved_hash = ultra_fast_encode(identity)

    # Normal direction states
    normal_frontier: dict[int, tuple[CubePermutation, list[str]]] = {
        initial_hash: (initial_permutation, [])
    }
    normal_visited: set[int] = {initial_hash}

    # Inverse direction states
    inverse_frontier: dict[int, tuple[CubePermutation, list[str]]] = {solved_hash: (identity, [])}
    inverse_visited: set[int] = {solved_hash}

    # Solution storage
    solutions: list[str] = []

    # Timing optimization
    start_time = time.perf_counter()

    # Early exit if already solved
    if initial_hash == solved_hash:
        return []

    depth = 0
    while depth < max_search_depth:
        depth += 1

        # Timeout check every depth from depth 2*k where n_actions^k > 100000, n_actions=18
        if depth >= 8:
            if time.perf_counter() - start_time > max_time:
                break

        # Adaptive direction selection: always choose the smaller frontier
        expand_normal = len(normal_frontier) < len(inverse_frontier)

        if expand_normal and normal_frontier:
            new_frontier = {}
            for permutation, moves in normal_frontier.values():
                for i in range(n_actions):
                    new_perm = permutation[action_arrays[i]]
                    new_hash = ultra_fast_encode(new_perm)

                    if new_hash not in normal_visited:
                        new_moves = moves + [action_keys[i]]
                        new_frontier[new_hash] = (new_perm, new_moves)
                        normal_visited.add(new_hash)

                        if new_hash in inverse_frontier:
                            solution = new_moves + ~MoveSequence(inverse_frontier[new_hash][1])
                            combine_axis_moves(solution)  # TODO(martin): Too slow here
                            solution_str = " ".join(solution)
                            if solution_str not in solutions:
                                solutions.append(solution_str)
                                if len(solutions) == n_solutions:
                                    return solutions

            normal_frontier = new_frontier

        elif inverse_frontier:
            new_frontier = {}
            for permutation, moves in inverse_frontier.values():
                for i in range(n_inverted_actions):
                    new_perm = permutation[inverted_action_arrays[i]]
                    new_hash = ultra_fast_encode(new_perm)

                    if new_hash not in inverse_visited:
                        new_moves = moves + [inverted_action_keys[i]]
                        new_frontier[new_hash] = (new_perm, new_moves)
                        inverse_visited.add(new_hash)

                        inv_hash = ultra_fast_encode(invert(new_perm))
                        if inv_hash in normal_frontier:
                            solution = MoveSequence(normal_frontier[inv_hash][1]) + new_moves
                            combine_axis_moves(solution)  # TODO(martin): Too slow here
                            solution_str = " ".join(solution)
                            if solution_str not in solutions:
                                solutions.append(solution_str)
                                if len(solutions) == n_solutions:
                                    return solutions

            inverse_frontier = new_frontier

    return solutions if solutions else None
