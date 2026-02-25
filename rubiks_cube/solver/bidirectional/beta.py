from __future__ import annotations

import time
from collections import defaultdict
from typing import TYPE_CHECKING

import numpy as np

from rubiks_cube.representation.utils import invert

if TYPE_CHECKING:
    from rubiks_cube.configuration.types import BoolArray
    from rubiks_cube.configuration.types import CubePattern
    from rubiks_cube.configuration.types import CubePermutation
    from rubiks_cube.configuration.types import PermutationValidator


def bidirectional_solver_many(
    initial_permutations: list[CubePermutation],
    actions: dict[str, CubePermutation],
    pattern: CubePattern,
    adj_matrix: BoolArray,
    min_search_depth: int,
    max_search_depth: int,
    max_solutions: int,
    max_solutions_per_root: int,
    validator: PermutationValidator | None,
    max_time: float,
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

    inverse_frontier: dict[bytes, tuple[int, ...]] = {solved_bytes: ()}
    inverse_visited: set[bytes] = {solved_bytes}
    alternative_inverse_paths: dict[bytes, list[tuple[int, ...]]] = {}

    start_time = time.perf_counter()
    depth = 0

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

        if len(normal_frontier) < len(inverse_frontier) and normal_frontier:
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
                            if add_solution(root_index=root_index, moves=candidate_moves):
                                if len(solutions) >= max_solutions:
                                    return solutions
                                if not root_has_capacity(root_index):
                                    break

            normal_visited.update(normal_new_frontier.keys())
            normal_frontier = normal_new_frontier

        elif inverse_frontier:
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


def bidirectional_solver(
    initial_permutation: CubePermutation,
    actions: dict[str, CubePermutation],
    pattern: CubePattern,
    adj_matrix: BoolArray,
    min_search_depth: int,
    max_search_depth: int,
    max_solutions: int,
    validator: PermutationValidator | None,
    max_time: float,
) -> list[list[str]] | None:
    """Optimized single-root bidirectional solver. Beta version."""
    initial_bytes = pattern[initial_permutation].tobytes()
    solved_bytes = pattern.tobytes()

    # Don't search if already solved
    if initial_bytes == solved_bytes:
        return []

    # Precompute canonical order of permutations and their inverses
    action_names = tuple(actions.keys())
    normal_perms = tuple(actions[name] for name in action_names)
    inverse_perms = tuple(invert(perm) for perm in normal_perms)
    n_actions = len(action_names)

    # Validate solution permutation
    def is_valid_solution(moves: tuple[int, ...]) -> bool:
        if validator is not None:
            candidate_perm = initial_permutation.copy()
            for i in moves:
                candidate_perm = candidate_perm[normal_perms[i]]
            return validator(candidate_perm)
        return True

    def construct_solution(move_idxs: tuple[int, ...]) -> list[str]:
        return [action_names[idx] for idx in move_idxs]

    # Frontiers and visited states
    normal_frontier: dict[bytes, tuple[int, ...]] = {initial_bytes: ()}
    inverse_frontier: dict[bytes, tuple[int, ...]] = {solved_bytes: ()}
    normal_visited: set[bytes] = {initial_bytes}
    inverse_visited: set[bytes] = {solved_bytes}
    alternative_normal_paths: dict[bytes, list[tuple[int, ...]]] = {}
    alternative_inverse_paths: dict[bytes, list[tuple[int, ...]]] = {}

    start_time = time.perf_counter()
    solutions: list[list[str]] = []
    depth = 0

    while depth < max_search_depth:
        depth += 1

        if time.perf_counter() - start_time > max_time:
            break

        if len(normal_frontier) < len(inverse_frontier) and normal_frontier:
            new_frontier: dict[bytes, tuple[int, ...]] = {}
            alternative_normal_paths = {}

            # Expand normal frontier
            for b, moves in normal_frontier.items():
                for i in range(n_actions):
                    if moves and not adj_matrix[moves[-1], i]:
                        continue

                    perm = np.frombuffer(b, dtype=np.uint8)
                    new_perm = perm[normal_perms[i]]
                    new_key = new_perm.tobytes()

                    if new_key in normal_visited:
                        continue

                    new_moves = (*moves, i)

                    if new_key in new_frontier:
                        alternative_normal_paths.setdefault(new_key, []).append(new_moves)
                    else:
                        new_frontier[new_key] = new_moves

                    # Check for bridges to inverse frontier
                    if depth >= min_search_depth and new_key in inverse_frontier:
                        for inverse_moves in [
                            inverse_frontier[new_key],
                            *alternative_inverse_paths.get(new_key, []),
                        ]:
                            if inverse_moves and not adj_matrix[i, inverse_moves[0]]:
                                continue

                            candidate_moves = (*new_moves, *inverse_moves)
                            if is_valid_solution(candidate_moves):
                                solutions.append(construct_solution(candidate_moves))
                                if len(solutions) == max_solutions:
                                    return solutions

            normal_visited.update(new_frontier.keys())
            normal_frontier = new_frontier

        elif inverse_frontier:
            new_frontier = {}
            alternative_inverse_paths = {}

            # Expand inverse frontier
            for b, moves in inverse_frontier.items():
                for i in range(n_actions):
                    if moves and not adj_matrix[i, moves[0]]:
                        continue

                    perm = np.frombuffer(b, dtype=np.uint8)
                    new_perm = perm[inverse_perms[i]]
                    new_key = new_perm.tobytes()

                    if new_key in inverse_visited:
                        continue

                    new_moves = (i, *moves)

                    if new_key in new_frontier:
                        alternative_inverse_paths.setdefault(new_key, []).append(new_moves)
                    else:
                        new_frontier[new_key] = new_moves

                    # Check for bridges to normal frontier
                    if depth >= min_search_depth and new_key in normal_frontier:
                        for normal_moves in [
                            normal_frontier[new_key],
                            *alternative_normal_paths.get(new_key, []),
                        ]:
                            if normal_moves and not adj_matrix[normal_moves[-1], i]:
                                continue

                            candidate_moves = (*normal_moves, *new_moves)
                            if is_valid_solution(candidate_moves):
                                solutions.append(construct_solution(candidate_moves))
                                if len(solutions) == max_solutions:
                                    return solutions

            inverse_visited.update(new_frontier.keys())
            inverse_frontier = new_frontier

    return solutions if solutions else None
