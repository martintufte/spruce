import time

import numpy as np

from rubiks_cube.configuration.types import BoolArray
from rubiks_cube.configuration.types import CubePattern
from rubiks_cube.configuration.types import CubePermutation
from rubiks_cube.representation.utils import invert


def bidirectional_solver(
    initial_permutation: CubePermutation,
    actions: dict[str, CubePermutation],
    pattern: CubePattern,
    canonical_matrix: BoolArray,
    max_search_depth: int,
    n_solutions: int,
    max_time: float,
) -> list[list[str]] | None:
    """Optimized bidirectional solver. Beta version.

    Args:
        initial_permutation (CubePermutation): The initial permutation.
        actions (dict[str, CubePermutation]): A dictionary of actions and permutations.
        pattern (CubePattern): The pattern that must match.
        canonical_matrix (BoolArray): Precomputed canonical move matrix.
        max_search_depth (int): The maximum depth.
        n_solutions (int): The number of solutions to find.
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

    def construct_solutions(solutions: list[tuple[int, ...]]) -> list[list[str]]:
        return [[action_names[idx] for idx in solution] for solution in solutions]

    # Frontiers and visited states
    normal_frontier: dict[bytes, tuple[int, ...]] = {initial_bytes: ()}
    inverse_frontier: dict[bytes, tuple[int, ...]] = {solved_bytes: ()}
    normal_visited: set[bytes] = {initial_bytes}
    inverse_visited: set[bytes] = {solved_bytes}
    alternative_normal_paths: dict[bytes, list[tuple[int, ...]]] = {}
    alternative_inverse_paths: dict[bytes, list[tuple[int, ...]]] = {}

    start_time = time.perf_counter()
    solutions: list[tuple[int, ...]] = []
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
                    if moves and not canonical_matrix[moves[-1], i]:
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
                    if new_key in inverse_frontier:
                        for inverse_moves in [
                            inverse_frontier[new_key],
                            *alternative_inverse_paths.get(new_key, []),
                        ]:
                            if inverse_moves and canonical_matrix[i, inverse_moves[0]]:
                                solutions.append((*new_moves, *inverse_moves))
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
                    if moves and not canonical_matrix[i, moves[0]]:
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
                    if new_key in normal_frontier:
                        for normal_moves in [
                            normal_frontier[new_key],
                            *alternative_normal_paths.get(new_key, []),
                        ]:
                            if normal_moves and not canonical_matrix[normal_moves[-1], i]:
                                continue
                            solutions.append((*normal_moves, *new_moves))
                            if len(solutions) == n_solutions:
                                return construct_solutions(solutions)

            inverse_visited.update(new_frontier.keys())
            inverse_frontier = new_frontier

    return construct_solutions(solutions) if solutions else None
