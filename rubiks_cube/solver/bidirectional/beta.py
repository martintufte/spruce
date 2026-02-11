from __future__ import annotations

import time
from typing import TYPE_CHECKING

import numpy as np

from rubiks_cube.representation.utils import invert

if TYPE_CHECKING:
    from rubiks_cube.configuration.types import BoolArray
    from rubiks_cube.configuration.types import CubePattern
    from rubiks_cube.configuration.types import CubePermutation
    from rubiks_cube.configuration.types import SolutionValidator


def bidirectional_solver(
    initial_permutation: CubePermutation,
    actions: dict[str, CubePermutation],
    pattern: CubePattern,
    adj_matrix: BoolArray,
    min_search_depth: int,
    max_search_depth: int,
    n_solutions: int,
    solution_validator: SolutionValidator | None,
    max_time: float,
) -> list[list[str]] | None:
    """Optimized bidirectional solver. Beta version.

    Args:
        initial_permutation (CubePermutation): The initial permutation.
        actions (dict[str, CubePermutation]): A dictionary of actions and permutations.
        pattern (CubePattern): The pattern that must match.
        adj_matrix (BoolArray): Adjacency matrix.
        min_search_depth (int): The minimum depth.
        max_search_depth (int): The maximum depth.
        n_solutions (int): The number of solutions to find.
        solution_validator (SolutionValidator | None, optional): Check for
            permutation that is performed for potential solutions. Defaults to None.
        max_time (float): Maximum time in seconds. Defaults to 60.0.

    Returns:
        list[list[str]] | None: List of solutions or None if no solutions found.
    """
    # Initialize search state
    initial_bytes = pattern[initial_permutation].tobytes()
    solved_bytes = pattern.tobytes()

    # Don't search if already solved
    if initial_bytes == solved_bytes:
        return []

    # Precompute canonical order of permutations and their inverses
    action_names = tuple(actions.keys())
    normal_perms = tuple(actions[name] for name in action_names)
    inverse_perms = tuple(invert(perm=perm) for perm in normal_perms)
    n_actions = len(action_names)

    # TODO(martin): Is there a faster way to reject solution?
    def is_valid(moves: tuple[int, ...]) -> bool:
        if solution_validator is not None:
            candidate_perm = initial_permutation.copy()
            for i in moves:
                candidate_perm = candidate_perm[normal_perms[i]]
            return solution_validator(candidate_perm)
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

        # Timeout check every depth from depth 8
        if depth >= 8 and (time.perf_counter() - start_time > max_time):
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
                            if inverse_moves and adj_matrix[i, inverse_moves[0]]:
                                candidate_moves = *new_moves, *inverse_moves

                                if is_valid(candidate_moves):
                                    solutions.append(construct_solution(candidate_moves))
                                    if len(solutions) == n_solutions:
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
                            candidate_moves = *normal_moves, *new_moves

                            if is_valid(candidate_moves):
                                solutions.append(construct_solution(candidate_moves))
                                if len(solutions) == n_solutions:
                                    return solutions

            inverse_visited.update(new_frontier.keys())
            inverse_frontier = new_frontier

    return solutions if solutions else None
