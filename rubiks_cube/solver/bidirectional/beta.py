from __future__ import annotations

import time
from collections import defaultdict
from typing import TYPE_CHECKING

import numpy as np

from rubiks_cube.representation.utils import invert

if TYPE_CHECKING:
    from rubiks_cube.configuration.types import BoolArray
    from rubiks_cube.configuration.types import PatternArray
    from rubiks_cube.configuration.types import PermutationArray
    from rubiks_cube.configuration.types import PermutationValidator


def precompute_inverse_frontier(
    pattern: PatternArray,
    actions: dict[str, PermutationArray],
    adj_matrix: BoolArray,
    depth: int,
) -> dict[bytes, tuple[int, ...]]:
    """Accumulate all inverse states reachable within `depth` steps from the solved state.

    Unlike the per-iteration frontier used in the bidirectional search, the returned dict
    contains every state at distance 0..depth (BFS shortest path). This makes it a
    complete lookup table that is independent of any scramble and can be reused across
    multiple searches that share the same solver (same pattern, actions, adj_matrix).
    """
    solved_bytes = pattern.tobytes()
    action_names = tuple(actions.keys())
    inverse_perms = tuple(invert(actions[name]) for name in action_names)
    n_actions = len(action_names)

    all_states: dict[bytes, tuple[int, ...]] = {solved_bytes: ()}
    current_layer: dict[bytes, tuple[int, ...]] = {solved_bytes: ()}

    for _ in range(depth):
        next_layer: dict[bytes, tuple[int, ...]] = {}

        for b, moves in current_layer.items():
            for action_idx in range(n_actions):
                if moves and not adj_matrix[action_idx, moves[0]]:
                    continue

                perm = np.frombuffer(b, dtype=np.uint8)
                new_perm = perm[inverse_perms[action_idx]]
                new_state = new_perm.tobytes()

                if new_state not in all_states and new_state not in next_layer:
                    next_layer[new_state] = (action_idx, *moves)

        all_states.update(next_layer)
        current_layer = next_layer

    return all_states


def bidirectional_solver(
    initial_permutations: list[PermutationArray],
    actions: dict[str, PermutationArray],
    pattern: PatternArray,
    adj_matrix: BoolArray,
    min_search_depth: int,
    max_search_depth: int,
    max_solutions: int,
    max_solutions_per_root: int,
    validator: PermutationValidator | None,
    max_time: float,
    prebuilt_inverse_frontier: dict[bytes, tuple[int, ...]] | None = None,
) -> list[tuple[int, list[str]]] | None:
    """Optimized multi-root bidirectional solver.

    Returns rooted solutions as `(root_index, moves)` pairs.
    """
    if max_solutions < 1 or max_solutions_per_root < 1:
        return None
    if len(initial_permutations) == 0:
        return None

    solved_bytes = pattern.tobytes()
    action_names = tuple(actions.keys())
    normal_perms = tuple(actions[name] for name in action_names)
    inverse_perms = tuple(invert(perm) for perm in normal_perms)
    n_actions = len(action_names)

    def is_valid_solution(root_index: int, moves: tuple[int, ...]) -> bool:
        if validator is None:
            return True
        candidate_perm = initial_permutations[root_index].copy()
        for action_idx in moves:
            candidate_perm = candidate_perm[normal_perms[action_idx]]
        return validator(candidate_perm)

    def construct_solution(move_idxs: tuple[int, ...]) -> list[str]:
        return [action_names[idx] for idx in move_idxs]

    solutions: list[tuple[int, list[str]]] = []
    solution_counts_by_root = [0] * len(initial_permutations)

    def root_has_capacity(root_index: int) -> bool:
        return solution_counts_by_root[root_index] < max_solutions_per_root

    def add_solution(root_index: int, moves: tuple[int, ...]) -> bool:
        if not root_has_capacity(root_index):
            return False
        if not is_valid_solution(root_index=root_index, moves=moves):
            return False
        solutions.append((root_index, construct_solution(moves)))
        solution_counts_by_root[root_index] += 1
        return True

    # Use rooted normal frontiers so each root can contribute solutions fairly.
    normal_frontier: dict[tuple[int, bytes], tuple[int, ...]] = {}
    normal_visited: set[tuple[int, bytes]] = set()
    alternative_normal_paths: dict[tuple[int, bytes], list[tuple[int, ...]]] = {}

    for root_index, initial_permutation in enumerate(initial_permutations):
        initial_bytes = pattern[initial_permutation].tobytes()
        if initial_bytes == solved_bytes:
            add_solution(root_index=root_index, moves=())
            if len(solutions) >= max_solutions:
                return solutions
            continue

        rooted_key = (root_index, initial_bytes)
        normal_frontier[rooted_key] = ()
        normal_visited.add(rooted_key)

    if not normal_frontier:
        return solutions if solutions else None

    # When a prebuilt frontier is supplied (all accumulated inverse states up to some depth),
    # use it as a fixed lookup table and only ever expand the normal frontier.  This avoids
    # recomputing the inverse expansion on every call when the same solver is reused across
    # many beam-search candidates.
    use_fixed_inverse = prebuilt_inverse_frontier is not None
    if use_fixed_inverse:
        inverse_frontier = dict(prebuilt_inverse_frontier)  # type: ignore[arg-type]
        inverse_visited = set(prebuilt_inverse_frontier.keys())  # type: ignore[union-attr]
    else:
        inverse_frontier = {solved_bytes: ()}
        inverse_visited = {solved_bytes}
    alternative_inverse_paths: dict[bytes, list[tuple[int, ...]]] = {}
    depth = 0

    start_time = time.perf_counter()

    while depth < max_search_depth:
        depth += 1

        if time.perf_counter() - start_time > max_time:
            break

        normal_frontier = {
            rooted_key: moves
            for rooted_key, moves in normal_frontier.items()
            if root_has_capacity(rooted_key[0])
        }
        if not normal_frontier:
            break

        if (use_fixed_inverse or len(normal_frontier) < len(inverse_frontier)) and normal_frontier:
            normal_new_frontier: dict[tuple[int, bytes], tuple[int, ...]] = {}
            alternative_normal_paths = {}

            # Expand normal frontier
            for (root_index, b), moves in normal_frontier.items():
                for action_idx in range(n_actions):
                    if moves and not adj_matrix[moves[-1], action_idx]:
                        continue

                    perm = np.frombuffer(b, dtype=np.uint8)
                    new_perm = perm[normal_perms[action_idx]]
                    new_state = new_perm.tobytes()
                    rooted_state = (root_index, new_state)

                    if rooted_state in normal_visited:
                        continue

                    new_moves = (*moves, action_idx)

                    if rooted_state in normal_new_frontier:
                        alternative_normal_paths.setdefault(rooted_state, []).append(new_moves)
                    else:
                        normal_new_frontier[rooted_state] = new_moves

                    # Bridge normal -> inverse
                    if depth >= min_search_depth and new_state in inverse_frontier:
                        for inverse_moves in [
                            inverse_frontier[new_state],
                            *alternative_inverse_paths.get(new_state, []),
                        ]:
                            if inverse_moves and not adj_matrix[action_idx, inverse_moves[0]]:
                                continue

                            candidate_moves = (*new_moves, *inverse_moves)
                            if len(candidate_moves) > max_search_depth:
                                continue
                            if add_solution(root_index=root_index, moves=candidate_moves):
                                if len(solutions) >= max_solutions:
                                    return solutions
                                if not root_has_capacity(root_index):
                                    break

            normal_visited.update(normal_new_frontier.keys())
            normal_frontier = normal_new_frontier

        elif not use_fixed_inverse and inverse_frontier:
            inverse_new_frontier: dict[bytes, tuple[int, ...]] = {}
            alternative_inverse_paths = {}

            normal_frontier_by_state: dict[bytes, list[tuple[int, tuple[int, ...]]]] = defaultdict(
                list
            )
            for (root_index, b), moves in normal_frontier.items():
                normal_frontier_by_state[b].append((root_index, moves))
                for alternative_moves in alternative_normal_paths.get((root_index, b), []):
                    normal_frontier_by_state[b].append((root_index, alternative_moves))

            # Expand inverse frontier
            for b, moves in inverse_frontier.items():
                for action_idx in range(n_actions):
                    if moves and not adj_matrix[action_idx, moves[0]]:
                        continue

                    perm = np.frombuffer(b, dtype=np.uint8)
                    new_perm = perm[inverse_perms[action_idx]]
                    new_state = new_perm.tobytes()

                    if new_state in inverse_visited:
                        continue

                    new_moves = (action_idx, *moves)

                    if new_state in inverse_new_frontier:
                        alternative_inverse_paths.setdefault(new_state, []).append(new_moves)
                    else:
                        inverse_new_frontier[new_state] = new_moves

                    # Bridge inverse -> normal
                    if depth >= min_search_depth and new_state in normal_frontier_by_state:
                        for root_index, normal_moves in normal_frontier_by_state[new_state]:
                            if not root_has_capacity(root_index):
                                continue
                            if normal_moves and not adj_matrix[normal_moves[-1], action_idx]:
                                continue

                            candidate_moves = (*normal_moves, *new_moves)
                            if add_solution(root_index=root_index, moves=candidate_moves):
                                if len(solutions) >= max_solutions:
                                    return solutions

            inverse_visited.update(inverse_new_frontier.keys())
            inverse_frontier = inverse_new_frontier

    return solutions if solutions else None
