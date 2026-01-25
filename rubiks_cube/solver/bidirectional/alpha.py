from __future__ import annotations

import logging
import time
from functools import lru_cache
from typing import TYPE_CHECKING
from typing import Final

import numpy as np

from rubiks_cube.formatting.regex import canonical_key
from rubiks_cube.representation.utils import invert

if TYPE_CHECKING:
    from rubiks_cube.configuration.types import CubePattern
    from rubiks_cube.configuration.types import CubePermutation

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
                        new_moves = [*moves, action_keys[i]]
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
                        new_moves = [action_keys[i], *moves]
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
                        new_moves = [*moves, i]
                        new_frontier[new_hash] = (new_perm, new_moves, i)
                        normal_visited.add(new_hash)

                        if new_hash in inverse_frontier:
                            new_moves = [*moves, i]
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
                        new_moves = [i, *moves]
                        new_frontier[new_hash] = (new_perm, new_moves, i)
                        inverse_visited.add(new_hash)

                        if new_hash in normal_frontier:
                            new_moves = [i, *moves]
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

                    new_moves = [*moves, i]

                    if new_key not in new_frontier:
                        new_frontier[new_key] = (new_perm, new_moves)
                    else:
                        existing_len = len(new_frontier[new_key][1])
                        if len(new_moves) > 1 and len(new_moves) == existing_len:
                            alternative_normal_paths.setdefault(new_key, []).append(new_moves)

                    # Check for bridges to inverse frontier
                    if new_key in inverse_frontier:
                        inv_candidates = [
                            inverse_frontier[new_key][1],
                            *alternative_inverse_paths.get(new_key, []),
                        ]
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

                    new_moves = [i, *moves]

                    if new_key not in new_frontier:
                        new_frontier[new_key] = (new_perm, new_moves)
                    else:
                        existing_len = len(new_frontier[new_key][1])
                        if len(new_moves) > 1 and len(new_moves) == existing_len:
                            alternative_inverse_paths.setdefault(new_key, []).append(new_moves)

                    # Check for bridges to normal frontier
                    if new_key in normal_frontier:
                        norm_candidates = [
                            normal_frontier[new_key][1],
                            *alternative_normal_paths.get(new_key, []),
                        ]
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


def bidirectional_solver_v7(
    initial_permutation: CubePermutation,
    actions: dict[str, CubePermutation],
    pattern: CubePattern,
    max_search_depth: int = 10,
    n_solutions: int = 1,
    max_time: float = 60.0,
) -> list[list[str]] | None:
    """Optimized bidirectional solver.

    Improvements over v6:
    - Simplified canonicality checking with unified is_canonical lookup table
    - More efficient pruning using inv_closed set instead of separate commutative/closed tables
    - Streamlined bridge detection logic with improved canonical move validation

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

    # Precompute pattern matches
    inv_closed = {tuple(identity), *(tuple(p) for p in normal_permutations)}

    # Precompute non-canonical pairs
    is_canonical: dict[tuple[int, int], bool] = {}
    for i, p_i in enumerate(normal_permutations):
        for j, p_j in enumerate(normal_permutations):
            p_ji = tuple(p_j[p_i])
            is_canonical[(i, j)] = not (p_ji in inv_closed or (i > j and p_ji == tuple(p_i[p_j])))

    # Encoding and decoding helpers
    def encode(permutation: CubePermutation) -> bytes:
        return pattern_uint8[permutation].tobytes()

    def construct_solutions(solutions: list[list[int]]) -> list[list[str]]:
        return [[action_names[idx] for idx in solution] for solution in solutions]

    # Initialize search state
    initial_bytes = encode(initial_permutation)
    solved_bytes = encode(identity)

    # Frontiers and visited states
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

        if len(normal_frontier) < len(inverse_frontier) and normal_frontier:
            new_frontier: dict[bytes, tuple[CubePermutation, list[int]]] = {}
            alternative_normal_paths = {}

            # Expand normal frontier
            for perm, moves in normal_frontier.values():
                for i in range(n_actions):
                    if moves and not is_canonical[moves[-1], i]:
                        continue

                    new_perm = perm[normal_permutations[i]]
                    new_key = encode(new_perm)

                    if new_key in normal_visited:
                        continue

                    new_moves = [*moves, i]

                    if new_key in new_frontier:
                        alternative_normal_paths.setdefault(new_key, []).append(new_moves)
                    else:
                        new_frontier[new_key] = (new_perm, new_moves)

                    # Check for bridges to inverse frontier
                    if new_key in inverse_frontier:
                        for inv_moves in [
                            inverse_frontier[new_key][1],
                            *alternative_inverse_paths.get(new_key, []),
                        ]:
                            if inv_moves and is_canonical[i, inv_moves[0]]:
                                solutions.append(new_moves + inv_moves)
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
                    if moves and not is_canonical[i, moves[0]]:
                        continue

                    new_perm = perm[inverted_permutations[i]]
                    new_key = encode(new_perm)

                    if new_key in inverse_visited:
                        continue

                    new_moves = [i, *moves]

                    if new_key in new_frontier:
                        alternative_inverse_paths.setdefault(new_key, []).append(new_moves)
                    else:
                        new_frontier[new_key] = (new_perm, new_moves)

                    # Check for bridges to normal frontier
                    if new_key in normal_frontier:
                        for norm_moves in [
                            normal_frontier[new_key][1],
                            *alternative_normal_paths.get(new_key, []),
                        ]:
                            if norm_moves and not is_canonical[norm_moves[-1], i]:
                                continue
                            solutions.append(norm_moves + new_moves)
                            if len(solutions) == n_solutions:
                                return construct_solutions(solutions)

            inverse_visited.update(new_frontier.keys())
            inverse_frontier = new_frontier

    if solutions:
        return construct_solutions(solutions)
    return None


def bidirectional_solver_v8(
    initial_permutation: CubePermutation,
    actions: dict[str, CubePermutation],
    pattern: CubePattern,
    max_search_depth: int,
    n_solutions: int,
    max_time: float = 60.0,
) -> list[list[str]] | None:
    """Optimized bidirectional solver.

    Improvements over v7:
    - Drop storing full permutation, only store the key pattern bytes.

    Optimizations v1 - v8:
    1. **Ultra-fast numpy-based state encoding**: Uses uint8 pattern arrays and tobytes()
       for maximum cache efficiency instead of string-based encoding
    2. **Adaptive direction selection**: Always expands the smaller frontier to minimize
       state space explosion and balance memory usage
    3. **Vectorized permutation operations**: Pre-computes all action arrays for direct
       numpy indexing operations, eliminating dictionary lookups during search
    4. **Canonical action ordering**: Sorts actions by canonical key to ensure consistent
       move sequences and deterministic solution generation
    5. **Non-canonical move pruning**: Pre-computes closed permutation pairs to eliminate
       redundant move sequences that result in identity or single moves
    6. **Alternative path tracking**: Stores multiple minimal-length paths to the same
       state to find all optimal solutions, not just the first discovered
    7. **Bytes-based state keys**: Uses bytes objects as dictionary keys for faster
       hashing and comparison than tuple-based approaches
    8. **Pre-computed inverse permutations**: Calculates and stores inverted actions
       upfront to avoid repeated inversion computations during inverse search
    9. **Smart timeout management**: Only checks elapsed time from depth 8+ where
       state space becomes large, avoiding frequent time.perf_counter() calls
    10. **Bidirectional bridge detection**: Efficiently detects when forward and backward
        searches meet by maintaining separate visited sets and checking intersections

    Args:
        initial_permutation (CubePermutation): The initial permutation.
        actions (dict[str, CubePermutation]): A dictionary of actions and permutations.
        pattern (CubePattern): The pattern that must match.
        max_search_depth (int, optional): The maximum depth.
        n_solutions (int, optional): The number of solutions to find. Defaults to 1.
        max_time (float, optional): Maximum time in seconds. Defaults to 60.0.

    Returns:
        list[list[str]] | None: List of solutions or None if no solutions found.
    """
    # Initialize base data
    identity = np.arange(initial_permutation.size, dtype=initial_permutation.dtype)
    actions = {name: actions[name] for name in sorted(actions.keys(), key=canonical_key)}

    # Precompute canonical order of permutations and their inverses
    action_names = tuple(actions.keys())
    normal_permutations = tuple(actions[name] for name in action_names)
    inverted_permutations = tuple(invert(perm) for perm in normal_permutations)
    n_actions = len(action_names)

    # Precompute pattern matches
    inv_closed = {tuple(identity), *(tuple(p) for p in normal_permutations)}

    # Precompute non-canonical pairs
    is_canonical: dict[tuple[int, int], bool] = {}
    for i, p_i in enumerate(normal_permutations):
        for j, p_j in enumerate(normal_permutations):
            p_ji = tuple(p_j[p_i])
            is_canonical[(i, j)] = not (p_ji in inv_closed or (i > j and p_ji == tuple(p_i[p_j])))

    def construct_solutions(solutions: list[list[int]]) -> list[list[str]]:
        return [[action_names[idx] for idx in solution] for solution in solutions]

    # Initialize search state
    initial_bytes = pattern[initial_permutation].tobytes()
    solved_bytes = pattern.tobytes()

    # Don't search if already solved
    if initial_bytes == solved_bytes:
        return []

    # Frontiers and visited states
    normal_frontier: dict[bytes, list[int]] = {initial_bytes: []}
    inverse_frontier: dict[bytes, list[int]] = {solved_bytes: []}
    normal_visited: set[bytes] = {initial_bytes}
    inverse_visited: set[bytes] = {solved_bytes}
    alternative_normal_paths: dict[bytes, list[list[int]]] = {}
    alternative_inverse_paths: dict[bytes, list[list[int]]] = {}

    start_time = time.perf_counter()
    solutions: list[list[int]] = []
    depth = 0

    while depth < max_search_depth:
        depth += 1

        # Timeout check every depth from depth 8
        if depth >= 8 and (time.perf_counter() - start_time > max_time):
            break

        if len(normal_frontier) < len(inverse_frontier) and normal_frontier:
            new_frontier: dict[bytes, list[int]] = {}
            alternative_normal_paths = {}

            # Expand normal frontier
            for b, moves in normal_frontier.items():
                for i in range(n_actions):
                    if moves and not is_canonical[moves[-1], i]:
                        continue

                    perm = np.frombuffer(b, dtype=np.uint8)
                    new_perm = perm[normal_permutations[i]]
                    new_key = new_perm.tobytes()

                    if new_key in normal_visited:
                        continue

                    new_moves = [*moves, i]

                    if new_key in new_frontier:
                        alternative_normal_paths.setdefault(new_key, []).append(new_moves)
                    else:
                        new_frontier[new_key] = new_moves

                    # Check for bridges to inverse frontier
                    if new_key in inverse_frontier:
                        for inv_moves in [
                            inverse_frontier[new_key],
                            *alternative_inverse_paths.get(new_key, []),
                        ]:
                            if inv_moves and is_canonical[i, inv_moves[0]]:
                                solutions.append(new_moves + inv_moves)
                                if len(solutions) == n_solutions:
                                    return construct_solutions(solutions)

            normal_visited.update(new_frontier.keys())
            normal_frontier = new_frontier

        elif inverse_frontier:
            new_frontier = {}
            alternative_inverse_paths = {}

            # Expand inverse frontier
            for b, moves in inverse_frontier.items():
                for i in range(n_actions):
                    if moves and not is_canonical[i, moves[0]]:
                        continue

                    perm = np.frombuffer(b, dtype=np.uint8)
                    new_perm = perm[inverted_permutations[i]]
                    new_key = new_perm.tobytes()

                    if new_key in inverse_visited:
                        continue

                    new_moves = [i, *moves]

                    if new_key in new_frontier:
                        alternative_inverse_paths.setdefault(new_key, []).append(new_moves)
                    else:
                        new_frontier[new_key] = new_moves

                    # Check for bridges to normal frontier
                    if new_key in normal_frontier:
                        for norm_moves in [
                            normal_frontier[new_key],
                            *alternative_normal_paths.get(new_key, []),
                        ]:
                            if norm_moves and not is_canonical[norm_moves[-1], i]:
                                continue
                            solutions.append(norm_moves + new_moves)
                            if len(solutions) == n_solutions:
                                return construct_solutions(solutions)

            inverse_visited.update(new_frontier.keys())
            inverse_frontier = new_frontier

    if solutions:
        return construct_solutions(solutions)
    return None
