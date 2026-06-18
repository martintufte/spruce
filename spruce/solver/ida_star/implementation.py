from __future__ import annotations

import math
import time
from typing import TYPE_CHECKING

from spruce.solver.branching import compute_branching_factor

if TYPE_CHECKING:
    from collections.abc import Callable

    from spruce.types import BoolArray
    from spruce.types import PatternArray
    from spruce.types import PermutationArray
    from spruce.types import PermutationValidator


def zero_heuristic(_: PermutationArray) -> int:
    return 0


def _depth_limit_from_branching(adj_matrix: BoolArray, max_searches: int = 10000) -> int:
    branching_factor = compute_branching_factor(adj_matrix)["expected"]
    if branching_factor <= 1.0:
        return max_searches
    return max(1, math.floor(math.log(max_searches) / math.log(branching_factor)))


def ida_star_solver(
    initial_permutations: list[PermutationArray],
    actions: dict[str, PermutationArray],
    pattern: PatternArray,
    adj_matrix: BoolArray,
    max_search_depth: int,
    max_solutions: int,
    max_solutions_per_root: int,
    validator: PermutationValidator | None,
    max_time: float,
    heuristic: Callable[[PermutationArray], int] = zero_heuristic,
) -> list[tuple[int, list[str]]] | None:
    """Search for solutions using iterative deepening depth-first search."""
    if max_solutions < 1 or max_solutions_per_root < 1:
        return None
    if len(initial_permutations) == 0:
        return None

    solved_bytes = pattern.tobytes()
    action_names = tuple(actions.keys())
    normal_perms = tuple(actions[name] for name in action_names)
    n_actions = len(action_names)

    def construct_solution(move_idxs: tuple[int, ...]) -> list[str]:
        return [action_names[idx] for idx in move_idxs]

    solutions: list[tuple[int, list[str]]] = []
    solution_counts_by_root = [0] * len(initial_permutations)
    seen_solutions_by_root: list[set[tuple[int, ...]]] = [set() for _ in initial_permutations]

    def root_has_capacity(root_index: int) -> bool:
        return solution_counts_by_root[root_index] < max_solutions_per_root

    def add_solution(root_index: int, permutation: PermutationArray, moves: tuple[int, ...]) -> bool:
        if not root_has_capacity(root_index) or moves in seen_solutions_by_root[root_index]:
            return False
        if validator is not None and not validator(permutation):
            return False
        solutions.append((root_index, construct_solution(moves)))
        solution_counts_by_root[root_index] += 1
        seen_solutions_by_root[root_index].add(moves)
        return True

    start_time = time.perf_counter()
    timed_out = False
    search_depth_limit = min(max_search_depth, _depth_limit_from_branching(adj_matrix))

    def search_depth(
        *,
        root_index: int,
        current_permutation: PermutationArray,
        current_state: bytes,
        g: int,
        bound: int,
        last_action_idx: int | None,
        moves: tuple[int, ...],
    ) -> None:
        nonlocal timed_out

        if timed_out or len(solutions) >= max_solutions or not root_has_capacity(root_index):
            return
        if time.perf_counter() - start_time > max_time:
            timed_out = True
            return

        if g + heuristic(current_permutation) > bound:
            return
        if current_state == solved_bytes:
            add_solution(root_index=root_index, permutation=current_permutation, moves=moves)
            return

        if g == bound:
            return

        for action_idx in range(n_actions):
            if last_action_idx is not None and not adj_matrix[last_action_idx, action_idx]:
                continue

            new_permutation = current_permutation[normal_perms[action_idx]]
            new_state = new_permutation.tobytes()
            search_depth(
                root_index=root_index,
                current_permutation=new_permutation,
                current_state=new_state,
                g=g + 1,
                bound=bound,
                last_action_idx=action_idx,
                moves=(*moves, action_idx),
            )

            if timed_out or len(solutions) >= max_solutions or not root_has_capacity(root_index):
                return

    for root_index, initial_permutation in enumerate(initial_permutations):
        if timed_out or len(solutions) >= max_solutions:
            break
        if not root_has_capacity(root_index):
            continue

        root_state = pattern[initial_permutation]
        root_state_bytes = root_state.tobytes()
        if root_state_bytes == solved_bytes:
            add_solution(root_index=root_index, permutation=root_state, moves=())
            continue

        for bound in range(search_depth_limit + 1):
            if timed_out or len(solutions) >= max_solutions or not root_has_capacity(root_index):
                break

            search_depth(
                root_index=root_index,
                current_permutation=root_state,
                current_state=root_state_bytes,
                g=0,
                bound=bound,
                last_action_idx=None,
                moves=(),
            )

    return solutions if solutions else None
