from __future__ import annotations

import time
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from spruce.types import BoolArray
    from spruce.types import PatternArray
    from spruce.types import PermutationArray
    from spruce.types import PermutationValidator


def unidirectional_solver(
    initial_permutations: list[PermutationArray],
    actions: dict[str, PermutationArray],
    pattern: PatternArray,
    adj_matrix: BoolArray,
    max_search_depth: int,
    max_solutions: int,
    max_solutions_per_root: int,
    validator: PermutationValidator | None,
    max_time: float,
) -> list[tuple[int, list[str]]] | None:
    """Multi-root unidirectional breadth-first solver.

    Expands a single frontier from the initial permutations and checks each new
    state against the solved pattern. Returns rooted solutions as
    `(root_index, moves)` pairs.
    """
    if max_solutions < 1 or max_solutions_per_root < 1:
        return None
    if len(initial_permutations) == 0:
        return None

    solved_bytes = pattern.tobytes()
    action_names = tuple(actions.keys())
    normal_perms = tuple(actions[name] for name in action_names)
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

    # Use rooted frontiers so each root can contribute solutions fairly.
    frontier: dict[tuple[int, bytes], tuple[int, ...]] = {}
    visited: set[tuple[int, bytes]] = set()

    for root_index, initial_permutation in enumerate(initial_permutations):
        initial_bytes = pattern[initial_permutation].tobytes()
        if initial_bytes == solved_bytes:
            add_solution(root_index=root_index, moves=())
            if len(solutions) >= max_solutions:
                return solutions
            continue

        rooted_key = (root_index, initial_bytes)
        frontier[rooted_key] = ()
        visited.add(rooted_key)

    depth = 0
    start_time = time.perf_counter()

    while depth < max_search_depth and frontier:
        depth += 1

        if time.perf_counter() - start_time > max_time:
            break

        frontier = {
            rooted_key: moves
            for rooted_key, moves in frontier.items()
            if root_has_capacity(rooted_key[0])
        }

        new_frontier: dict[tuple[int, bytes], tuple[int, ...]] = {}

        for (root_index, b), moves in frontier.items():
            for action_idx in range(n_actions):
                if moves and not adj_matrix[moves[-1], action_idx]:
                    continue

                perm = np.frombuffer(b, dtype=np.uint8)
                new_perm = perm[normal_perms[action_idx]]
                new_state = new_perm.tobytes()
                new_moves = (*moves, action_idx)

                if new_state == solved_bytes and add_solution(
                    root_index=root_index,
                    moves=new_moves,
                ):
                    if len(solutions) >= max_solutions:
                        return solutions
                    if not root_has_capacity(root_index):
                        break

                # Keep expanding through pattern-matching states: a validator may
                # have rejected the match, and deeper solutions can pass through it.
                rooted_state = (root_index, new_state)
                if rooted_state in visited or rooted_state in new_frontier:
                    continue
                new_frontier[rooted_state] = new_moves

        visited.update(new_frontier.keys())
        frontier = new_frontier

    return solutions if solutions else None
