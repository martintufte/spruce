import logging
import time
from typing import Final

import numpy as np

from rubiks_cube.configuration.types import CubePattern
from rubiks_cube.configuration.types import CubePermutation
from rubiks_cube.formatting.regex import canonical_key
from rubiks_cube.representation.utils import invert

LOGGER: Final = logging.getLogger(__name__)


def backtrack_solutions(
    intersection_states: list[bytes],
    normal_visited: dict[bytes, tuple[list[int], set[int]]],
    inverse_visited: dict[bytes, tuple[list[int], set[int]]],
    normal_permutations: tuple[CubePermutation, ...],
    inverted_permutations: tuple[CubePermutation, ...],
    action_names: tuple[str, ...],
) -> list[list[str]]:
    """Backtrack solutions from intersection states.

    Args:
        intersection_states (list[bytes]): The intersection states.
        normal_visited (dict[bytes, tuple[list[int], set[int]]]): The normal visited states.
        inverse_visited (dict[bytes, tuple[list[int], set[int]]]): The inverse visited states.
        normal_permutations (tuple[CubePermutation, ...]): The normal permutations.
        inverted_permutations (tuple[CubePermutation, ...]): The inverted permutations.
        action_names (tuple[str, ...]): The action names.

    Returns:
        list[list[str]]: The backtracked solutions.
    """
    solutions: list[list[str]] = []

    for state_bytes in intersection_states:
        normal_moves, normal_redundant = normal_visited[state_bytes]
        inverse_moves, inverse_redundant = inverse_visited[state_bytes]

        # Build solutions from intersection state
        if redundant_moves := normal_redundant | inverse_redundant:
            solution = [
                "{"
                + ", ".join(
                    [action_names[idx] for idx in sorted(redundant_moves, key=canonical_key)]
                )
                + "}"
            ]
        else:
            solution = []

        # Backtrack normal moves
        perm = np.frombuffer(state_bytes, dtype=np.uint8)
        while normal_moves:
            # Add first move
            move_idx = normal_moves.pop(0)
            solution.insert(0, action_names[move_idx])

            # Update permutation and state to parent
            parent_perm = perm[inverted_permutations[move_idx]]
            parent_state = parent_perm.tobytes()

            normal_moves, redundant_moves = normal_visited[parent_state]
            if redundant_moves:
                solution.insert(
                    0,
                    [
                        "{"
                        + ", ".join(
                            [
                                action_names[idx]
                                for idx in sorted(redundant_moves, key=canonical_key)
                            ]
                        )
                        + "}"
                    ],
                )
            perm = parent_perm

        # Backtrack inverse moves
        perm = np.frombuffer(state_bytes, dtype=np.uint8)
        while inverse_moves:
            # Add first move
            move_idx = inverse_moves.pop(0)
            solution.append(action_names[move_idx])

            # Update permutation and state to parent
            parent_perm = perm[normal_permutations[move_idx]]
            parent_state = parent_perm.tobytes()

            inverse_moves, redundant_moves = inverse_visited[parent_state]
            if redundant_moves:
                solution.append(
                    "{"
                    + ", ".join(
                        [action_names[idx] for idx in sorted(redundant_moves, key=canonical_key)]
                    )
                    + "}"
                )
            perm = parent_perm

        solutions.append(solution)

    return solutions


def bidirectional_solver_alt(
    initial_permutation: CubePermutation,
    actions: dict[str, CubePermutation],
    pattern: CubePattern,
    max_search_depth: int,
    n_solutions: int,
    max_time: float = 60.0,
) -> list[list[str]] | None:
    """Backtracking bidirectional solver. v9.

    Improvements over v8:
    - Use backtracking instead of storing alternative paths.
    - Store parent moves and redundant moves separately.
    - Include redundant moves in solution notation with curly brackets.

    Args:
        initial_permutation (CubePermutation): The initial permutation.
        actions (dict[str, CubePermutation]): A dictionary of actions and permutations.
        pattern (CubePattern): The pattern that must match.
        max_search_depth (int, optional): The maximum depth.
        n_solutions (int, optional): The number of solutions to find. Defaults to 1.
        max_time (float, optional): Maximum time in seconds. Defaults to 60.0.

    Returns:
        list[list[str]] | None: Intersection bytes or None if no solutions found.
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

    # Initialize search state
    initial_bytes = pattern[initial_permutation].tobytes()
    solved_bytes = pattern.tobytes()

    # Don't search if already solved
    if initial_bytes == solved_bytes:
        return []

    # Frontiers store (parent_moves, redundant_moves)
    normal_frontier: dict[bytes, tuple[list[int], set[int]]] = {initial_bytes: ([], set())}
    inverse_frontier: dict[bytes, tuple[list[int], set[int]]] = {solved_bytes: ([], set())}

    normal_visited: dict[bytes, tuple[list[int], set[int]]] = normal_frontier
    inverse_visited: dict[bytes, tuple[list[int], set[int]]] = inverse_frontier

    start_time = time.perf_counter()
    intersection_states: list[bytes] = []
    depth = 0

    while depth < max_search_depth:
        depth += 1

        # Timeout check every depth from depth 8
        if depth >= 8 and (time.perf_counter() - start_time > max_time):
            break

        if len(normal_frontier) <= len(inverse_frontier) and normal_frontier:
            new_frontier: dict[bytes, tuple[list[int], set[int]]] = {}

            # Expand normal frontier
            for state_bytes, (parent_moves, _redundant_moves) in normal_frontier.items():
                for i in range(n_actions):
                    # Check canonicality for any previous move
                    if parent_moves and not any(is_canonical[move, i] for move in parent_moves):
                        continue

                    # Apply move
                    perm = np.frombuffer(state_bytes, dtype=np.uint8)
                    new_state = perm[normal_permutations[i]].tobytes()

                    # Case 1: Explored state at lower depth
                    if new_state in normal_visited:
                        continue

                    # Case 2: New state is redundant
                    if new_state == state_bytes:
                        new_frontier[state_bytes][1].add(i)
                        continue

                    # Case 3: Explored state at frontier
                    if new_state in new_frontier:
                        new_frontier[new_state][0].append(i)
                        continue

                    # Case 4: New state
                    new_frontier[new_state] = ([i], set())

                    # Check for intersection with inverse frontier
                    if new_state in inverse_frontier:
                        # Check for canonicality between last normal move and first inverse move
                        inv_parent_moves, _ = inverse_frontier[new_state]
                        if any(is_canonical[i, move] for move in inv_parent_moves):
                            intersection_states.append(new_state)
                            if len(intersection_states) == n_solutions:
                                normal_visited.update(new_frontier)
                                return backtrack_solutions(
                                    intersection_states,
                                    normal_visited,
                                    inverse_visited,
                                    normal_permutations,
                                    inverted_permutations,
                                    action_names,
                                )

            normal_visited.update(new_frontier)
            normal_frontier = new_frontier

        elif inverse_frontier:
            new_frontier = {}

            # Expand inverse frontier
            for state_bytes, (parent_moves, _redundant_moves) in inverse_frontier.items():
                for i in range(n_actions):
                    # Check canonicality for any previous move
                    if parent_moves and not any(is_canonical[i, move] for move in parent_moves):
                        continue

                    # Apply move
                    perm = np.frombuffer(state_bytes, dtype=np.uint8)
                    new_state = perm[inverted_permutations[i]].tobytes()

                    # Case 1: Explored state at lower depth
                    if new_state in inverse_visited:
                        continue

                    # Case 2: New state is redundant
                    if new_state == state_bytes:
                        new_frontier[state_bytes][1].add(i)
                        continue

                    # Case 3: Explored state at frontier
                    if new_state in new_frontier:
                        new_frontier[new_state][0].append(i)
                        continue

                    # Case 4: New state
                    new_frontier[new_state] = ([i], set())

                    # Check for intersection with normal frontier
                    if new_state in normal_frontier:
                        # Check for canonicality between last normal move and first inverse move
                        norm_parent_moves, _ = normal_frontier[new_state]
                        if any(is_canonical[move, i] for move in norm_parent_moves):
                            intersection_states.append(new_state)
                            if len(intersection_states) >= n_solutions:
                                inverse_visited.update(new_frontier)
                                return backtrack_solutions(
                                    intersection_states,
                                    normal_visited,
                                    inverse_visited,
                                    normal_permutations,
                                    inverted_permutations,
                                    action_names,
                                )

            inverse_visited.update(new_frontier)
            inverse_frontier = new_frontier

    # Construct solutions by backtracking
    if intersection_states:
        return backtrack_solutions(
            intersection_states,
            normal_frontier,
            inverse_frontier,
            normal_permutations,
            inverted_permutations,
            action_names,
        )

    return None
