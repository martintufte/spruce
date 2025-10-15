import logging
import time
from typing import Final

import numpy as np

from rubiks_cube.configuration.types import CubePattern
from rubiks_cube.configuration.types import CubePermutation
from rubiks_cube.formatting.regex import canonical_key
from rubiks_cube.representation.utils import invert

LOGGER: Final = logging.getLogger(__name__)


# TODO(martin): Before this function is done:
# - Make into a class
# - Fix duplicate solutions bug, should not be possible with depth first search
# - Add dead move solution findings, e.g. "B2 U F" is a solution to eo-fb if "U F" is
def bidirectional_solver(
    initial_permutation: CubePermutation,
    actions: dict[str, CubePermutation],
    pattern: CubePattern,
    max_search_depth: int = 10,
    n_solutions: int = 1,
    max_time: float = 60.0,
) -> list[list[str]] | None:
    """Optimized bidirectional solver.

    Optimizations:
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
    is_not_canonical: dict[tuple[int, int], bool] = {}
    for i, p_i in enumerate(normal_permutations):
        for j, p_j in enumerate(normal_permutations):
            p_ji = tuple(p_j[p_i])
            is_not_canonical[(i, j)] = p_ji in inv_closed or (i > j and p_ji == tuple(p_i[p_j]))

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
