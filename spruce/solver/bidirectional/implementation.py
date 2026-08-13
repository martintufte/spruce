"""Bidirectional search over a permutation group.

Given a set of actions (permutations labelled by a symbol), search for a word over
those actions that maps each initial permutation onto a state matching the target
pattern. The search expands a forward frontier from the initial permutations and a
backward frontier from the target simultaneously, and reports a solution whenever the
two frontiers meet.
"""

from __future__ import annotations

import time
from collections import defaultdict
from typing import TYPE_CHECKING

import numpy as np

from spruce.representation.utils import invert

if TYPE_CHECKING:
    from spruce.types import BoolArray
    from spruce.types import MoveSymbol
    from spruce.types import PatternArray
    from spruce.types import PermutationArray
    from spruce.types import PermutationValidator


def bidirectional_solver(  # noqa: C901
    initial_permutations: list[PermutationArray],
    actions: dict[MoveSymbol, PermutationArray],
    pattern: PatternArray,
    adj_matrix: BoolArray,
    max_search_depth: int,
    max_solutions: int,
    max_solutions_per_root: int,
    validator: PermutationValidator | None,
    max_time: float,
) -> list[tuple[int, list[MoveSymbol]]] | None:
    """Optimized multi-root bidirectional solver.

    Returns rooted solutions as `(root_index, word)` pairs.
    """
    if max_solutions < 1 or max_solutions_per_root < 1:
        return None

    if len(initial_permutations) == 0:
        return None

    target_bytes = pattern.tobytes()
    symbols = tuple(actions.keys())
    action_perms = tuple(actions[symbol] for symbol in symbols)
    inverted_action_perms = tuple(invert(perm) for perm in action_perms)
    n_actions = len(symbols)

    # Precompute adjacency as python structures to avoid numpy scalar lookups in the hot loop
    adj = adj_matrix.tolist()
    all_action_idxs = list(range(n_actions))
    allowed_after = [[j for j in all_action_idxs if adj[i][j]] for i in all_action_idxs]
    allowed_before = [[i for i in all_action_idxs if adj[i][j]] for j in all_action_idxs]

    # Stack the allowed permutations per predecessor action so a state expands all its
    # successors with a single take + tobytes, sliced per action afterwards.
    state_size = len(target_bytes)
    forward_expand = [
        (allowed, np.array([action_perms[j] for j in allowed])) for allowed in allowed_after
    ]
    backward_expand = [
        (allowed, np.array([inverted_action_perms[i] for i in allowed]))
        for allowed in allowed_before
    ]
    expand_all_forward = (all_action_idxs, np.array(action_perms))
    expand_all_backward = (all_action_idxs, np.array(inverted_action_perms))

    def is_valid_solution(root_index: int, path: tuple[int, ...]) -> bool:
        if validator is None:
            return True
        candidate_perm = initial_permutations[root_index].copy()
        for action_idx in path:
            candidate_perm = candidate_perm[action_perms[action_idx]]
        return validator(candidate_perm)

    def construct_word(path: tuple[int, ...]) -> list[MoveSymbol]:
        return [symbols[action_idx] for action_idx in path]

    solutions: list[tuple[int, list[MoveSymbol]]] = []
    solution_counts_by_root = [0] * len(initial_permutations)

    def root_has_capacity(root_index: int) -> bool:
        return solution_counts_by_root[root_index] < max_solutions_per_root

    def add_solution(root_index: int, path: tuple[int, ...]) -> bool:
        if not root_has_capacity(root_index):
            return False
        if not is_valid_solution(root_index=root_index, path=path):
            return False
        solutions.append((root_index, construct_word(path)))
        solution_counts_by_root[root_index] += 1
        return True

    # Use rooted forward frontiers so each root can contribute solutions fairly.
    forward_frontier: dict[tuple[int, bytes], tuple[int, ...]] = {}
    forward_visited: set[tuple[int, bytes]] = set()
    alternative_forward_paths: dict[tuple[int, bytes], list[tuple[int, ...]]] = {}

    for root_index, initial_permutation in enumerate(initial_permutations):
        initial_bytes = pattern[initial_permutation].tobytes()
        if initial_bytes == target_bytes:
            add_solution(root_index=root_index, path=())
            if len(solutions) >= max_solutions:
                return solutions
            continue

        rooted_key = (root_index, initial_bytes)
        forward_frontier[rooted_key] = ()
        forward_visited.add(rooted_key)

    if not forward_frontier:
        return solutions if solutions else None

    backward_frontier: dict[bytes, tuple[int, ...]] = {target_bytes: ()}
    backward_visited: set[bytes] = {target_bytes}
    alternative_backward_paths: dict[bytes, list[tuple[int, ...]]] = {}

    depth = 0
    start_time = time.perf_counter()

    while depth < max_search_depth:
        depth += 1

        if time.perf_counter() - start_time > max_time:
            break

        forward_frontier = {
            rooted_key: path
            for rooted_key, path in forward_frontier.items()
            if root_has_capacity(rooted_key[0])
        }
        if not forward_frontier or not backward_frontier:
            break

        if len(forward_frontier) < len(backward_frontier):
            forward_new_frontier: dict[tuple[int, bytes], tuple[int, ...]] = {}
            alternative_forward_paths = {}

            for (root_index, state_bytes), path in forward_frontier.items():
                state = np.frombuffer(state_bytes, dtype=np.uint8)
                allowed, stacked_perms = forward_expand[path[-1]] if path else expand_all_forward
                raw = state.take(stacked_perms).tobytes()
                for pos, action_idx in enumerate(allowed):
                    new_state = raw[pos * state_size : (pos + 1) * state_size]
                    rooted_state = (root_index, new_state)

                    if rooted_state in forward_visited:
                        continue

                    new_path = (*path, action_idx)

                    if rooted_state in forward_new_frontier:
                        alternative_forward_paths.setdefault(rooted_state, []).append(new_path)
                    else:
                        forward_new_frontier[rooted_state] = new_path

                    if new_state in backward_frontier:
                        for backward_path in [
                            backward_frontier[new_state],
                            *alternative_backward_paths.get(new_state, []),
                        ]:
                            if not root_has_capacity(root_index):
                                break
                            if backward_path and not adj[action_idx][backward_path[0]]:
                                continue
                            candidate_path = (*new_path, *backward_path)
                            if (
                                add_solution(root_index=root_index, path=candidate_path)
                                and len(solutions) >= max_solutions
                            ):
                                return solutions

            forward_visited.update(forward_new_frontier.keys())
            forward_frontier = forward_new_frontier

        else:
            backward_new_frontier: dict[bytes, tuple[int, ...]] = {}
            alternative_backward_paths = {}

            forward_frontier_by_state: dict[bytes, list[tuple[int, tuple[int, ...]]]] = defaultdict(
                list,
            )
            for (root_index, state_bytes), path in forward_frontier.items():
                forward_frontier_by_state[state_bytes].append((root_index, path))
                for alternative_path in alternative_forward_paths.get(
                    (root_index, state_bytes), []
                ):
                    forward_frontier_by_state[state_bytes].append((root_index, alternative_path))

            for state_bytes, path in backward_frontier.items():
                state = np.frombuffer(state_bytes, dtype=np.uint8)
                allowed, stacked_perms = backward_expand[path[0]] if path else expand_all_backward
                raw = state.take(stacked_perms).tobytes()
                for pos, action_idx in enumerate(allowed):
                    new_state = raw[pos * state_size : (pos + 1) * state_size]

                    if new_state in backward_visited:
                        continue

                    new_path = (action_idx, *path)

                    if new_state in backward_new_frontier:
                        alternative_backward_paths.setdefault(new_state, []).append(new_path)
                    else:
                        backward_new_frontier[new_state] = new_path

                    if new_state in forward_frontier_by_state:
                        for root_index, forward_path in forward_frontier_by_state[new_state]:
                            if not root_has_capacity(root_index):
                                continue
                            if forward_path and not adj[forward_path[-1]][action_idx]:
                                continue

                            candidate_path = (*forward_path, *new_path)
                            if (
                                add_solution(root_index=root_index, path=candidate_path)
                                and len(solutions) >= max_solutions
                            ):
                                return solutions

            backward_visited.update(backward_new_frontier.keys())
            backward_frontier = backward_new_frontier

    return solutions if solutions else None
