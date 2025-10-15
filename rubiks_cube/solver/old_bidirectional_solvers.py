import logging
import time
from functools import lru_cache
from typing import Final

import numpy as np

from rubiks_cube.configuration.types import CubePattern
from rubiks_cube.configuration.types import CubePermutation
from rubiks_cube.formatting.regex import canonical_key
from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.move.sequence import cleanup
from rubiks_cube.move.sequence import combine_axis_moves
from rubiks_cube.move.utils import invert_move
from rubiks_cube.representation.utils import invert

LOGGER: Final = logging.getLogger(__name__)


@lru_cache(maxsize=128)
def build_pruning_table(
    action_keys: tuple[str, ...],
    action_arrays: tuple[tuple[int, ...], ...],
    identity: tuple[int, ...],
) -> dict[int, tuple[int, ...]]:
    """Build lookup table for last-move pruning using closed permutations.

    This function is cached to avoid recomputing the same pruning table
    for identical action spaces.

    Args:
        action_keys: Tuple of action names (for caching key)
        action_arrays: Tuple of action permutation arrays (converted to tuples for hashing)
        identity: Identity permutation as tuple (for caching key)

    Returns:
        Dictionary mapping each move index to tuple of allowed move indices after it
    """
    n_actions = len(action_keys)

    # Convert back to numpy arrays for computation
    action_arrays_np = tuple(np.array(arr) for arr in action_arrays)
    identity_np = np.array(identity)

    # Pre-compute bridge closure check
    closed_perms = {tuple(perm): True for perm in [identity_np, *action_arrays_np]}

    # Build pruning table
    pruning_table = {}
    for i in range(n_actions):
        moves_to_avoid = set()

        # Check all possible next moves
        for j in range(n_actions):
            # Compute the combined effect of move i followed by move j
            combined_perm = action_arrays_np[j][action_arrays_np[i]]

            # If the combination is closed (identity or single move), avoid it
            if tuple(combined_perm) in closed_perms:
                moves_to_avoid.add(j)

        # Store allowed moves as tuple instead of moves to avoid
        allowed_moves = tuple(j for j in range(n_actions) if j not in moves_to_avoid)
        pruning_table[i] = allowed_moves

    # Add sentinel for no last move
    pruning_table[-1] = tuple(range(n_actions))

    return pruning_table


def bidirectional_solver_v1(
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


def bidirectional_solver_v4(
    initial_permutation: CubePermutation,
    actions: dict[str, CubePermutation],
    pattern: CubePattern,
    max_search_depth: int = 10,
    n_solutions: int = 1,
    max_time: float = 60.0,
) -> list[list[str]] | None:
    """Blazingly-fast bidirectional solver with adaptive direction selection.

    Modification of v3:
    - Reduce calls to ultra_fast_encode from 2 to 1 per new permutation in inverse direction
    - Preinvert the actions for the inverse direction to avoid recomputation
    - Store the reverse inverted move sequence for inverse direction to avoid inverting
    - Faster check that two bridge actions are not closed in the action space

    Args:
        initial_permutation (CubePermutation): The initial permutation.
        actions (dict[str, CubePermutation]): A dictionary of actions and permutations.
        pattern (CubePattern): The pattern that must match.
        max_search_depth (int, optional): The maximum depth. Defaults to 10.
        n_solutions (int, optional): The number of solutions to find. Defaults to 1.
        max_time (float, optional): Maximum time in seconds. Defaults to 60.0.

    Returns:
        list[list[str]] | None: List of solutions or None if no solutions found.
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
    inverted_actions = {key: invert(action) for key, action in actions.items()}
    inverted_action_arrays = tuple(inverted_actions[key] for key in action_keys)

    # Use arrays for faster access patterns
    identity = np.arange(initial_permutation.size, dtype=initial_permutation.dtype)
    initial_hash = ultra_fast_encode(initial_permutation)
    solved_hash = ultra_fast_encode(identity)

    # Normal direction states
    normal_frontier: dict[int, tuple[CubePermutation, list[str]]] = {
        initial_hash: (initial_permutation, [])
    }
    normal_visited: set[int] = {initial_hash}

    # Inverse direction states
    inverse_frontier: dict[int, tuple[CubePermutation, list[str]]] = {solved_hash: (identity, [])}
    inverse_visited: set[int] = {solved_hash}

    # Pre-compute bridge closure check
    closed_perms = {tuple(perm): True for perm in [identity, *action_arrays]}

    # Solution storage
    solutions: list[list[str]] = []

    # Timing optimization
    start_time = time.perf_counter()

    # Early exit if already solved
    if initial_hash == solved_hash:
        return []

    depth = 0
    while depth < max_search_depth:
        depth += 1

        # Timeout check every depth from depth 8
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
                            if depth > 1:
                                bridge_perm = action_arrays[i][
                                    actions[inverse_frontier[new_hash][1][0]]
                                ]
                                if tuple(bridge_perm) in closed_perms:
                                    continue
                            solutions.append(new_moves + inverse_frontier[new_hash][1])
                            if len(solutions) == n_solutions:
                                return solutions

            normal_frontier = new_frontier

        elif inverse_frontier:
            new_frontier = {}
            for permutation, moves in inverse_frontier.values():
                for i in range(n_actions):
                    new_perm = permutation[inverted_action_arrays[i]]
                    new_hash = ultra_fast_encode(new_perm)

                    if new_hash not in inverse_visited:
                        new_moves = [action_keys[i]] + moves
                        new_frontier[new_hash] = (new_perm, new_moves)
                        inverse_visited.add(new_hash)

                        if new_hash in normal_frontier:
                            if depth > 1:
                                bridge_perm = inverted_action_arrays[i][
                                    actions[normal_frontier[new_hash][1][-1]]
                                ]
                                if tuple(bridge_perm) in closed_perms:
                                    continue
                            solutions.append(normal_frontier[new_hash][1] + new_moves)
                            if len(solutions) == n_solutions:
                                return solutions

            inverse_frontier = new_frontier

    return solutions if solutions else None


def bidirectional_solver_v5(
    initial_permutation: CubePermutation,
    actions: dict[str, CubePermutation],
    pattern: CubePattern,
    max_search_depth: int = 10,
    n_solutions: int = 1,
    max_time: float = 60.0,
) -> list[list[str]] | None:
    """Ultra-optimized bidirectional solver with 1-move pruning and integer encoding.

    Modification of v4:
    - 1-move pruning table: Eliminate moves that are closed under the last move
    - Integer encoding optimization: Store move indices of actions during search
    - Ignore solutions with commutative moves

    Args:
        initial_permutation (CubePermutation): The initial permutation.
        actions (dict[str, CubePermutation]): A dictionary of actions and permutations.
        pattern (CubePattern): The pattern that must match.
        max_search_depth (int, optional): The maximum depth. Defaults to 10.
        n_solutions (int, optional): The number of solutions to find. Defaults to 1.
        max_time (float, optional): Maximum time in seconds. Defaults to 60.0.

    Returns:
        list[list[str]] | None: List of solutions or None if no solutions found.
    """
    # Ultra-fast encoding using numpy operations (uint8 for maximum cache efficiency)
    pattern_uint8 = np.asarray(pattern, dtype=np.uint8)

    def ultra_fast_encode(permutation: CubePermutation) -> int:
        """Ultra-fast encoding using numpy operations."""
        return hash(pattern_uint8[permutation].tobytes())

    # Pre-compute all action permutations for vectorized operations
    action_names = tuple(actions.keys())
    action_perms = tuple(actions[name] for name in action_names)
    inverted_actions = {name: invert(action) for name, action in actions.items()}
    inverted_action_perms = tuple(inverted_actions[name] for name in action_names)

    # Pre-compute commutative groups
    commutative_groups: list[set[int]] = []
    for i, perm_i in enumerate(action_perms):
        if any(i in group for group in commutative_groups):
            continue
        group = {i}
        for j, perm_j in enumerate(action_perms):
            if tuple(perm_j[perm_i]) == tuple(perm_i[perm_j]):  # Commutative check
                group.add(j)
        commutative_groups.append(group)

    commutative_map: dict[int, int] = {}  # Map action index to group index
    for i, group in enumerate(commutative_groups):
        for j in group:
            commutative_map[j] = i

    # Helper to filter out commutative starting and ending moves
    def commutative_start(moves: list[int]) -> list[int]:
        if not moves:
            return []
        if len(moves) == 1:
            return moves
        # Always keep the first move
        group = commutative_map[moves[0]]
        # Return the first consecutive moves in the same group
        out = [moves[0]]
        for move in moves[1:]:
            if commutative_map[move] != group:
                break
            out.append(move)
        return out

    def commutative_end(moves: list[int]) -> list[int]:
        if not moves:
            return []
        if len(moves) == 1:
            return moves
        # Always keep the last move
        group = commutative_map[moves[-1]]
        # Return the last consecutive moves in the same group
        out = [moves[-1]]
        for move in reversed(moves[:-1]):
            if commutative_map[move] != group:
                break
            out.append(move)
        return list(out)

    # Function to construct solutions from integer indices
    def construct_solutions(solutions: list[list[int]]) -> list[list[str]]:
        return [[action_names[idx] for idx in solution] for solution in solutions]

    # Use permutations for faster access to patterns
    identity = np.arange(initial_permutation.size, dtype=initial_permutation.dtype)

    # Build 1-move pruning table
    pruning_table = build_pruning_table(
        action_names, tuple(tuple(perm) for perm in action_perms), tuple(identity)
    )
    initial_hash = ultra_fast_encode(initial_permutation)
    solved_hash = ultra_fast_encode(identity)

    # Normal direction states - store integer indices for moves, not strings
    normal_frontier: dict[int, tuple[CubePermutation, list[int], int]] = {
        initial_hash: (initial_permutation, [], -1)  # -1 means no last move
    }
    normal_visited: set[int] = {initial_hash}

    # Inverse direction states - store integer indices for moves, not strings
    inverse_frontier: dict[int, tuple[CubePermutation, list[int], int]] = {
        solved_hash: (identity, [], -1)  # -1 means no last move
    }
    inverse_visited: set[int] = {solved_hash}

    start_time = time.perf_counter()
    if initial_hash == solved_hash:
        return []

    solutions: list[list[int]] = []
    depth = 0
    while depth < max_search_depth:
        depth += 1

        # Timeout check every depth from depth 8
        if depth >= 8:
            if time.perf_counter() - start_time > max_time:
                break

        # Adaptive direction selection: always choose the smaller frontier
        expand_normal = len(normal_frontier) < len(inverse_frontier)

        if expand_normal and normal_frontier:
            new_frontier = {}
            for perm, moves, last_move in normal_frontier.values():
                for i in pruning_table[last_move]:
                    new_perm = perm[action_perms[i]]
                    new_hash = ultra_fast_encode(new_perm)

                    if new_hash not in normal_visited:
                        new_moves = moves + [i]
                        new_frontier[new_hash] = (new_perm, new_moves, i)
                        normal_visited.add(new_hash)

                        if new_hash in inverse_frontier:
                            new_moves = moves + [i]
                            inv_moves = inverse_frontier[new_hash][1]

                            # Check for commutative move pruning
                            if any(
                                end not in pruning_table[start]
                                for start in commutative_end(new_moves)
                                for end in commutative_start(inv_moves)
                            ):
                                continue

                            solutions.append(new_moves + inv_moves)
                            if len(solutions) == n_solutions:
                                return construct_solutions(solutions)

            normal_frontier = new_frontier

        elif inverse_frontier:
            new_frontier = {}
            for perm, moves, last_move in inverse_frontier.values():
                for i in pruning_table[last_move]:
                    new_perm = perm[inverted_action_perms[i]]
                    new_hash = ultra_fast_encode(new_perm)

                    if new_hash not in inverse_visited:
                        new_moves = [i] + moves
                        new_frontier[new_hash] = (new_perm, new_moves, i)
                        inverse_visited.add(new_hash)

                        if new_hash in normal_frontier:
                            new_moves = [i] + moves
                            norm_moves = normal_frontier[new_hash][1]

                            # Check for commutative move pruning
                            if any(
                                end not in pruning_table[start]
                                for start in commutative_end(norm_moves)
                                for end in commutative_start(new_moves)
                            ):
                                continue

                            solutions.append(norm_moves + new_moves)
                            if len(solutions) == n_solutions:
                                return construct_solutions(solutions)

            inverse_frontier = new_frontier

    # Convert any remaining solutions to strings before returning
    if solutions:
        return construct_solutions(solutions)
    return None


def bidirectional_solver_v6(
    initial_permutation: CubePermutation,
    actions: dict[str, CubePermutation],
    pattern: CubePattern,
    max_search_depth: int = 10,
    n_solutions: int = 1,
    max_time: float = 60.0,
) -> list[list[str]] | None:
    """Ultra-optimized bidirectional solver.

    Major updates for correctness over v5:
    - Add canonical ordering of actions to ensure consistent move sequences
    - Store alternative paths for each state to find all minimal solutions
    - Improved solution construction to include all alternative minimal paths
    - More general names for variables and functions

    Args:
        initial_permutation (CubePermutation): The initial permutation.
        actions (dict[str, CubePermutation]): A dictionary of actions and permutations.
        pattern (CubePattern): The pattern that must match.
        max_search_depth (int, optional): The maximum depth. Defaults to 10.
        n_solutions (int, optional): The number of solutions to find. Defaults to 1.
        max_time (float, optional): Maximum time in seconds. Defaults to 60.0.

    Returns:
        list[list[str]] | None: List of solutions or None if no solutions found.
    """
    # Initialize base data
    identity = np.arange(initial_permutation.size, dtype=initial_permutation.dtype)
    pattern_uint8 = np.asarray(pattern, dtype=np.uint8).copy()
    actions = {name: actions[name] for name in sorted(actions.keys(), key=canonical_key)}

    # Precompute canonical order of permutations and their inverses
    action_names = tuple(actions.keys())
    normal_permutations = tuple(actions[name] for name in action_names)
    inverted_permutations = tuple(invert(perm) for perm in normal_permutations)
    n_actions = len(action_names)

    # Precompute commutative pairs
    is_commutative: dict[tuple[int, int], bool] = {}
    for i, perm_i in enumerate(normal_permutations):
        is_commutative[(i, i)] = False
        for j, perm_j in enumerate(normal_permutations[i + 1 :], start=i + 1):
            is_comm = tuple(perm_j[perm_i]) == tuple(perm_i[perm_j])
            is_commutative[(i, j)] = is_comm
            is_commutative[(j, i)] = is_comm

    # Precompute closed and inverse pairs
    is_closed: dict[tuple[int, int], bool] = {}
    for i, perm_i in enumerate(normal_permutations):
        for j, perm_j in enumerate(normal_permutations[i:], start=i):
            new_perm = perm_j[perm_i]
            is_closed[(i, j)] = tuple(new_perm) in (
                tuple(identity),
                *(tuple(p) for p in normal_permutations),
            )
            is_closed[(j, i)] = is_closed[(i, j)]

    # Precompute non-canonical pairs
    is_not_canonical: dict[tuple[int, int], bool] = {}
    for i in range(n_actions):
        for j in range(n_actions):
            is_not_canonical[(i, j)] = (i > j and is_commutative[(i, j)]) or is_closed[(i, j)]

    # Encoding and decoding helpers
    def encode(permutation: CubePermutation) -> bytes:
        return pattern_uint8[permutation].tobytes()

    def construct_solutions(solutions: list[list[int]]) -> list[list[str]]:
        return [[action_names[idx] for idx in solution] for solution in solutions]

    # Initialize search state
    initial_bytes = encode(initial_permutation)
    solved_bytes = encode(identity)

    normal_frontier: dict[bytes, tuple[CubePermutation, list[int]]] = {
        initial_bytes: (initial_permutation, [])
    }
    inverse_frontier: dict[bytes, tuple[CubePermutation, list[int]]] = {
        solved_bytes: (identity, [])
    }

    normal_visited: set[bytes] = {initial_bytes}
    inverse_visited: set[bytes] = {solved_bytes}

    alternative_normal_paths: dict[bytes, list[list[int]]] = {}
    alternative_inverse_paths: dict[bytes, list[list[int]]] = {}

    start_time = time.perf_counter()

    # Trivial case: already solved
    if initial_bytes == solved_bytes:
        return []

    solutions: list[list[int]] = []
    depth = 0

    while depth < max_search_depth:
        depth += 1

        # Timeout check every depth from depth 8
        if depth >= 8 and (time.perf_counter() - start_time > max_time):
            break

        expand_normal = len(normal_frontier) < len(inverse_frontier)

        if expand_normal and normal_frontier:
            new_frontier: dict[bytes, tuple[CubePermutation, list[int]]] = {}
            alternative_normal_paths = {}

            # Expand normal frontier
            for perm, moves in normal_frontier.values():
                for i in range(n_actions):
                    if moves and is_not_canonical[moves[-1], i]:
                        continue

                    new_perm = perm[normal_permutations[i]]
                    new_key = encode(new_perm)

                    if new_key in normal_visited:
                        continue

                    new_moves = moves + [i]

                    if new_key not in new_frontier:
                        new_frontier[new_key] = (new_perm, new_moves)
                    else:
                        existing_len = len(new_frontier[new_key][1])
                        if len(new_moves) > 1 and len(new_moves) == existing_len:
                            alternative_normal_paths.setdefault(new_key, []).append(new_moves)

                    # Check for bridges to inverse frontier
                    if new_key in inverse_frontier:
                        inv_candidates = [
                            inverse_frontier[new_key][1]
                        ] + alternative_inverse_paths.get(new_key, [])
                        for inv_moves in inv_candidates:
                            if inv_moves and is_not_canonical[i, inv_moves[0]]:
                                continue
                            solutions.append(new_moves + inv_moves)
                            if len(solutions) == n_solutions:
                                return construct_solutions(solutions)

                    # Check for alternative inverse paths
                    if new_key in alternative_inverse_paths:
                        for alt_inv_moves in alternative_inverse_paths[new_key]:
                            if alt_inv_moves and is_not_canonical[i, alt_inv_moves[0]]:
                                continue
                            solutions.append(new_moves + alt_inv_moves)
                            if len(solutions) == n_solutions:
                                return construct_solutions(solutions)

            normal_visited.update(new_frontier.keys())
            normal_frontier = new_frontier

        elif inverse_frontier:
            new_frontier = {}
            alternative_inverse_paths = {}

            # Expand inverse frontier
            for perm, moves in inverse_frontier.values():
                for i in range(n_actions):
                    if moves and is_not_canonical[i, moves[0]]:
                        continue

                    new_perm = perm[inverted_permutations[i]]
                    new_key = encode(new_perm)

                    if new_key in inverse_visited:
                        continue

                    new_moves = [i] + moves

                    if new_key not in new_frontier:
                        new_frontier[new_key] = (new_perm, new_moves)
                    else:
                        existing_len = len(new_frontier[new_key][1])
                        if len(new_moves) > 1 and len(new_moves) == existing_len:
                            alternative_inverse_paths.setdefault(new_key, []).append(new_moves)

                    # Check for bridges to normal frontier
                    if new_key in normal_frontier:
                        norm_candidates = [
                            normal_frontier[new_key][1]
                        ] + alternative_normal_paths.get(new_key, [])
                        for norm_moves in norm_candidates:
                            if norm_moves and is_not_canonical[norm_moves[-1], i]:
                                continue
                            solutions.append(norm_moves + new_moves)
                            if len(solutions) == n_solutions:
                                return construct_solutions(solutions)

                    # Check for alternative normal paths
                    if new_key in alternative_normal_paths:
                        for alt_norm_moves in alternative_normal_paths[new_key]:
                            if alt_norm_moves and is_not_canonical[alt_norm_moves[-1], i]:
                                continue
                            solutions.append(alt_norm_moves + new_moves)
                            if len(solutions) == n_solutions:
                                return construct_solutions(solutions)

            inverse_visited.update(new_frontier.keys())
            inverse_frontier = new_frontier

    # Return found solutions, if any
    if solutions:
        return construct_solutions(solutions)
    return None
