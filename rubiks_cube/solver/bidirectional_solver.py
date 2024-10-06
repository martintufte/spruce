import logging
import re
import time

import numpy as np

from rubiks_cube.configuration import CUBE_SIZE
from rubiks_cube.configuration.enumeration import Piece
from rubiks_cube.configuration.type_definitions import CubeState
from rubiks_cube.move.generator import MoveGenerator
from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.move.sequence import cleanup
from rubiks_cube.state import get_rubiks_cube_state
from rubiks_cube.state.permutation import create_permutations
from rubiks_cube.state.permutation import get_identity_permutation
from rubiks_cube.state.permutation import get_piece_mask
from rubiks_cube.state.permutation import unorientate_mask
from rubiks_cube.state.permutation.utils import invert
from rubiks_cube.state.tag.patterns import CubePattern
from rubiks_cube.state.tag.patterns import get_cubexes

LOGGER = logging.getLogger(__name__)


def encode(permutation: CubeState, pattern: CubeState) -> str:
    """Encode a permutation into a string using a pattern.

    Args:
        permutation (CubeState): Cube state.
        pattern (CubeState): Pattern.

    Returns:
        str: Encoded string.
    """
    return str(pattern[permutation])


def bidirectional_solver(
    initial_permutation: CubeState,
    actions: dict[str, CubeState],
    pattern: CubeState,
    max_search_depth: int = 10,
    n_solutions: int = 1,
) -> list[str] | None:
    """Bidirectional solver for the Rubik's cube.
    It uses a breadth-first search from both states to find the shortest path
    between two states and returns the optimal solution.

    Args:
        initial_permutation (CubeState): The initial permutation.
        actions (dict[str, CubeState]): A dictionary of actions and
            permutations.
        pattern (CubeState): The pattern that must match.
        max_search_depth (int, optional): The maximum depth. Defaults to 10.
        n_solutions (int, optional): The number of solutions to find.
            Defaults to 1.

    Returns:
        list[str] | None: List of solutions. Empty list if already solved. None if no solution.
    """

    initial_str = encode(initial_permutation, pattern)
    last_states_normal: dict[str, tuple[CubeState, list[str]]] = {
        initial_str: (initial_permutation, [])
    }
    searched_states_normal: dict[str, tuple[CubeState, list[str]]] = {
        initial_str: (initial_permutation, [])
    }

    # Last searched permutations and all searched states on inverse permutation
    identity = np.arange(len(initial_permutation))
    solved_str = encode(identity, pattern)
    last_states_inverse: dict[str, tuple[CubeState, list[str]]] = {solved_str: (identity, [])}
    searched_states_inverse: dict[str, tuple[CubeState, list[str]]] = {solved_str: (identity, [])}

    # Store the solutions as cleaned sequence for keys and unclear for values
    solutions: dict[str, str] = {}

    # Check if the initial state is solved
    LOGGER.info("Searching for solution..")
    LOGGER.info("Search depth: 0")
    if initial_str in searched_states_inverse:
        LOGGER.info("Found solution")
        return []

    for i in range(max_search_depth // 2):
        # Expand last searched states on normal permutation
        LOGGER.info(f"Search depth: {2*i + 1}")
        new_searched_states_normal: dict[str, tuple[CubeState, list[str]]] = {}
        for permutation, move_list in last_states_normal.values():
            for move, action in actions.items():
                new_permutation = permutation[action]
                new_state_str = encode(new_permutation, pattern)
                if new_state_str not in searched_states_normal:
                    new_move_list = move_list + [move]
                    new_searched_states_normal[new_state_str] = (
                        new_permutation,
                        new_move_list,
                    )

                    # Check if inverse permutation is searched
                    new_inverse_str = encode(new_permutation, pattern)
                    if new_inverse_str in last_states_inverse:
                        solution = MoveSequence(new_move_list) + ~MoveSequence(
                            last_states_inverse[new_inverse_str][1]
                        )
                        solution_cleaned = str(cleanup(solution))
                        if solution_cleaned not in solutions:
                            solutions[solution_cleaned] = str(solution)
                            LOGGER.info(f"Found solution ({len(solutions)}/{n_solutions})")
                        if len(solutions) == n_solutions:
                            return list(solutions.values())

        searched_states_normal.update(new_searched_states_normal)
        last_states_normal = new_searched_states_normal

        # Expand last searched states on inverse permutation
        LOGGER.info(f"Search depth: {2*i + 2}")
        new_searched_states_inverse: dict[str, tuple[CubeState, list[str]]] = {}
        for permutation, move_list in last_states_inverse.values():
            for move, action in actions.items():
                new_permutation = permutation[action]
                new_state_str = encode(new_permutation, pattern)
                if new_state_str not in searched_states_inverse:
                    new_move_list = move_list + [move]
                    new_searched_states_inverse[new_state_str] = (
                        new_permutation,
                        new_move_list,
                    )

                    # Check if inverse permutation is searched
                    new_inverse_str = encode(invert(new_permutation), pattern)
                    if new_inverse_str in last_states_normal:
                        solution = MoveSequence(
                            last_states_normal[new_inverse_str][1] + new_move_list
                        )
                        solution_cleaned = str(cleanup(solution))
                        if solution_cleaned not in solutions:
                            solutions[solution_cleaned] = str(solution)
                            LOGGER.info(f"Found solution ({len(solutions)}/{n_solutions})")
                        if len(solutions) == n_solutions:
                            return list(solutions.values())

        searched_states_inverse.update(new_searched_states_inverse)
        last_states_inverse = new_searched_states_inverse

    if len(solutions) == 0:
        return None
    return list(solutions.values())


def expand_generator(sequence: MoveSequence, cube_size: int) -> list[MoveSequence]:
    """This function expands a sequence into a list of sequences if the move is
    a sequence of length one and the move is in the permutations and the move
    is not a double move.

    Args:
        sequence (MoveSequence): The move sequence to expand.

    Returns:
        list[str]: List of expanded move sequences.
    """
    permutations = create_permutations(cube_size=cube_size)

    if len(sequence.moves) != 1:
        return [sequence]

    move = sequence.moves[0]
    if move not in permutations:
        return [sequence]

    pattern = re.compile(r"^([23456789]?[LRFBUD][w])(['2]?)$|^([LRFBUDxyzMES])(['2]?)$")
    match = pattern.match(move)

    if match is not None:
        core = match.group(1) or match.group(3)
        modifier = match.group(2) or match.group(4)

        if modifier == "2":
            return [sequence]

        return [
            MoveSequence(f"{core}"),
            MoveSequence(f"{core}'"),
            MoveSequence(f"{core}2"),
        ]

    return [sequence]


def get_action_space(
    generator: MoveGenerator,
    cube_size: int = CUBE_SIZE,
) -> dict[str, CubeState]:
    """Get the action space from a generator.
    Offset the action space with the initial permutation if given.

    Args:
        generator (MoveGenerator): Move generator.
        offset (CubeState): Permutation to offset the action space.
        cube_size (int): Size of the cube.

    Returns:
        dict[str, CubeState]: Action space.
    """

    actions = {}
    for sequence in generator:
        for sequence in expand_generator(sequence, cube_size=cube_size):
            permutation = get_rubiks_cube_state(
                sequence=sequence,
                cube_size=cube_size,
            )
            actions[str(sequence)] = permutation
    return actions


def create_pattern_state(pattern: CubePattern) -> CubeState:
    """Create a goal state from a pattern using the mask and orientations.

    Args:
        pattern (CubePattern): Pattern state.

    Returns:
        CubeState: Pattern goal state.
    """

    goal_state = get_identity_permutation(cube_size=pattern.size)

    if pattern.mask is not None:
        goal_state[~pattern.mask] = max(goal_state) + 1
    for orientation in pattern.orientations:
        goal_state[orientation] = max(goal_state) + 1

    # Reindex the goal state
    indexes = sorted(list(set(list(goal_state))))
    for i, index in enumerate(indexes):
        goal_state[goal_state == index] = i

    return goal_state


def reindex(
    initial_state: CubeState,
    actions: dict[str, CubeState],
    pattern: CubeState,
    boolean_mask: CubeState,
) -> tuple[CubeState, dict[str, CubeState], CubeState]:
    """Reindex the permutations and action space.

    Args:
        initial_state (CubeState): Initial permutation.
        actions (dict[str, CubeState]): Action space.
        pattern (CubeState): Pattern.
        boolean_mask (CubeState): Boolean mask.

    Returns:
        tuple[CubeState, dict[str, CubeState], CubeState]: Reindexed
            initial permutation, action space and pattern.
    """
    initial_state = initial_state[boolean_mask]
    for action in actions:
        actions[action] = actions[action][boolean_mask]
    pattern = pattern[boolean_mask]

    for new_index, index in enumerate(np.where(boolean_mask)[0]):
        initial_state[initial_state == index] = new_index
        for action in actions:
            actions[action][actions[action] == index] = new_index

    return initial_state, actions, pattern


def optimize_indecies(
    initial_state: CubeState,
    actions: dict[str, CubeState],
    pattern: CubeState,
    cube_size: int = CUBE_SIZE,
) -> tuple[CubeState, dict[str, CubeState], CubeState]:
    """Reduce the complexity of the permutations and action space.

    1. Identify indecies that are not affected by the action space.
    2. Identify conserved orientations of corners and edges.
    3. Identify piece types that are not in the pattern.
    4. Reindex the permutations and action space.
    5. Split into disjoint action groups and remove bijections
    6. Reindex the permutations and action space.

    Args:
        initial_permutation (CubeState): Initial permutation.
        actions (dict[str, CubeState]): Action space.
        pattern (CubeState): Pattern.

    Returns:
        tuple[CubeState, dict[str, CubeState], CubeState]: Optimized
            initial permutation, action space and pattern that can be used
            equivalently by the solver.
    """
    initial_length = len(initial_state)
    # This is a boolean mask that will be used to remove indecies
    boolean_mask = np.zeros_like(initial_state, dtype=bool)

    # 1. Identify the indexes that are not affected by the action space
    identity = np.arange(len(initial_state))
    for permutation in actions.values():
        boolean_mask |= identity != permutation

    # 2. Identify conserved orientations of corners and edges
    for piece in [Piece.corner, Piece.edge]:
        piece_mask = get_piece_mask(piece, cube_size=cube_size)
        union_mask = boolean_mask & piece_mask

        while np.any(union_mask):
            # Initialize a mask for the first piece in the union mask
            mask = np.zeros_like(identity, dtype=bool)
            mask[np.argmax(union_mask)] = True

            # Find all the other indecies that the piece can reach
            while True:
                new_mask = mask.copy()
                for permutation in actions.values():
                    new_mask |= mask[permutation]
                # No new indecies found, break the loop
                if np.all(mask == new_mask):
                    break
                mask = new_mask

            # No orientation found for the piece, cannot remove the indexes
            if np.all(mask == union_mask):
                break

            unorientated_mask = unorientate_mask(mask, cube_size=cube_size)
            union_mask &= ~unorientated_mask
            boolean_mask[unorientated_mask ^ mask] = False

    # 3. Identify piece types that are not in the pattern
    for piece in [Piece.center, Piece.corner, Piece.edge]:
        piece_mask = get_piece_mask(piece, cube_size=cube_size)
        if np.unique(pattern[piece_mask]).size == 1:
            boolean_mask &= ~piece_mask

    idx_set = set(np.where(boolean_mask)[0])
    for permutation in actions.values():
        assert idx_set == set(permutation[boolean_mask]), "Action space and boolean mask mismatch."
    assert idx_set == set(
        initial_state[boolean_mask]
    ), "Initial state cannot be solved with the action space."

    # 4. Reindex the permutations and action space
    initial_state, actions, pattern = reindex(
        initial_state=initial_state,
        actions=actions,
        pattern=pattern,
        boolean_mask=boolean_mask,
    )

    # 5. Split into disjoint action groups and remove bijections
    groups = []
    identity = np.arange(len(initial_state))
    all_indecies = set(identity)
    while all_indecies:
        # Initialize a mask for a random idx
        group_mask = np.zeros_like(initial_state, dtype=bool)
        group_mask[all_indecies.pop()] = True

        # Find all the other indecies that the piece can reach
        while True:
            new_group_mask = group_mask.copy()
            for permutation in actions.values():
                new_group_mask |= group_mask[permutation]
            # No new indecies found, break the loop
            if np.all(group_mask == new_group_mask):
                break
            group_mask = new_group_mask

        group_idecies = np.where(group_mask)[0]
        all_indecies -= set(group_idecies)
        groups.append(group_idecies)

    # Remove groups that are bijections of each other
    bijective_groups: list[tuple[int, ...]] = []
    for i, group in enumerate(groups):
        added_group = False
        group_mapping = {idx: i for i, idx in enumerate(group)}
        for j, other_group in enumerate(groups[(i + 1) :]):

            # Don't add groups that are already bijective
            already_bijective = False
            for bijective_group in bijective_groups:
                if i in bijective_group and i + 1 + j in bijective_group:
                    already_bijective = True
                    break

            # Don't compare groups of different sizes, they are not injective
            if not len(group) == len(other_group) or already_bijective:
                continue
            group_identity = np.arange(len(group))
            other_group_mapping = {idx: i for i, idx in enumerate(other_group)}
            for permutation in actions.values():
                group_permutation = permutation[group]
                other_group_permutation = permutation[other_group]

                # Map to the new indecies
                group_permutation = np.array([group_mapping[idx] for idx in group_permutation])
                other_group_permutation = np.array(
                    [other_group_mapping[idx] for idx in other_group_permutation]
                )
                if not np.array_equal(
                    group_permutation[invert(other_group_permutation)], group_identity
                ):
                    break
            else:
                insert_idx = -1
                for group_idx, bijective_group in enumerate(bijective_groups):
                    if i in bijective_group:
                        new_bijective_group = (*bijective_group, i + 1 + j)
                        insert_idx = group_idx
                        break
                if insert_idx == -1:
                    bijective_groups.append((i, i + 1 + j))
                else:
                    bijective_groups[insert_idx] = new_bijective_group
                added_group = True
                break
        if not added_group:
            found = False
            for bijective_group in bijective_groups:
                if i in bijective_group:
                    found = True
                    break
            if not found:
                bijective_groups.append((i,))

    # Only keep the first group of each bijective group
    boolean_mask = np.zeros_like(initial_state, dtype=bool)
    for bijective_group in bijective_groups:
        boolean_mask[groups[bijective_group[0]]] = True

    # 6. Reindex the permutations and action space
    if not np.all(boolean_mask):
        initial_state, actions, pattern = reindex(
            initial_state=initial_state,
            actions=actions,
            pattern=pattern,
            boolean_mask=boolean_mask,
        )

    LOGGER.info(f"Optimizer reduced from {initial_length} to {len(initial_state)} indecies.")
    return initial_state, actions, pattern


def get_matchable_pattern(step: str | None = None, cube_size: int = CUBE_SIZE) -> CubeState:
    """Setup the pattern and initial state.

    Args:
        cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.
        step (str, optional): Step to solve. Defaults to None.
    """
    if step is not None and cube_size == 3:
        cubexes = get_cubexes(cube_size=cube_size)
        if step not in cubexes:
            raise ValueError("Cannot find the step. Will not solve the step.")
        cubex = cubexes[step].patterns[0]
        pattern = create_pattern_state(cubex)
    else:
        pattern = get_identity_permutation(cube_size=cube_size)

    return pattern


def find_offset(
    initial_state: CubeState,
    actions: dict[str, CubeState],
    cube_size: int = CUBE_SIZE,
) -> tuple[str, CubeState] | tuple[None, None]:
    """Find the offset between the initial state and the pattern.

    Args:
        initial_state (CubeState): Initial state.
        actions (dict[str, CubeState]): Action space.

    Returns:
        CubeState | None: Offset between the initial state and the pattern.
    """
    # Find the part of the cube that is not affected by the action space
    identity = np.arange(len(initial_state))
    boolean_mask = np.zeros_like(initial_state, dtype=bool)
    for permutation in actions.values():
        boolean_mask |= identity != permutation
    boolean_mask = ~boolean_mask

    standard_rotations = {
        "UF": "",
        "UL": "y'",
        "UB": "y2",
        "UR": "y",
        "FU": "x y2",
        "FL": "x y'",
        "FD": "x",
        "FR": "x y",
        "RU": "z' y'",
        "RF": "z'",
        "RD": "z' y",
        "RB": "z' y2",
        "BU": "x'",
        "BL": "x' y'",
        "BD": "x' y2",
        "BR": "x' y",
        "LU": "z y",
        "LF": "z",
        "LD": "z y'",
        "LB": "z y2",
        "DF": "z2",
        "DL": "x2 y'",
        "DB": "x2",
        "DR": "x2 y",
    }

    for rotation in standard_rotations.values():
        rotated_state = get_rubiks_cube_state(
            sequence=MoveSequence(rotation),
            cube_size=cube_size,
        )
        if np.array_equal(rotated_state[boolean_mask], initial_state[boolean_mask]):
            return rotation, rotated_state
    return None, None


def solve_step(
    sequence: MoveSequence,
    generator: MoveGenerator = MoveGenerator("<L, R, U, D, F, B>"),
    step: str | None = None,
    max_search_depth: int = 10,
    n_solutions: int = 1,
    goal_sequence: MoveSequence = MoveSequence(),
    search_inverse: bool = False,
    cube_size: int = CUBE_SIZE,
) -> list[MoveSequence] | None:
    """Solve a single step of the Rubik's cube.

    Args:
        sequence (MoveSequence): Sequence to scramble the cube.
        generator (MoveGenerator, optional): Generator for actions at each step.
            Defaults to MoveGenerator("<L, R, U, D, F, B>").
        step (str | None, optional): Step to solve. Defaults to None, which is the solved state.
        max_search_depth (int, optional): Maximum search depth. Defaults to 10.
        n_solutions (int, optional): Number of solutions to return. Defaults to 1.
        goal_sequence (MoveSequence, optional): Sequence to scramble the goal state.
            Defaults to MoveSequence().
        search_inverse (bool, optional): Whether to search on the inverse. Defaults to False.
        cube_size (int, optional): Size of the cube to solve. Defaults to CUBE_SIZE.

    Returns:
        list[MoveSequence] | None: List of solutions. None if no solution.
    """

    # Initial state
    inverted_goal_state = get_rubiks_cube_state(
        sequence=goal_sequence,
        cube_size=cube_size,
        invert_after=True,
    )
    initial_state = get_rubiks_cube_state(
        sequence=sequence,
        initial_state=inverted_goal_state,
        invert_after=search_inverse,
        cube_size=cube_size,
    )

    # Get the matchable pattern
    pattern = get_matchable_pattern(step=step, cube_size=cube_size)

    # Get the action space
    actions = get_action_space(generator=generator, cube_size=cube_size)

    # Find the rotation offset
    _, offset = find_offset(initial_state, actions, cube_size=cube_size)
    if offset is not None:
        inv_offset = invert(offset)
        initial_state = initial_state[inv_offset]
        for action in actions:
            actions[action] = offset[actions[action]][inv_offset]
        pattern = pattern[inv_offset]

    # Check if the cube is already solved
    if np.array_equal(pattern[initial_state], pattern):
        return []

    # Optimize the indecies in the permutations and pattern
    initial_state, actions, pattern = optimize_indecies(
        initial_state=initial_state,
        actions=actions,
        pattern=pattern,
        cube_size=cube_size,
    )

    # Solve the step using a bidirectional search
    t = time.time()
    solutions = bidirectional_solver(
        initial_permutation=initial_state,
        actions=actions,
        pattern=pattern,
        max_search_depth=max_search_depth,
        n_solutions=n_solutions,
    )
    n_solutions = len(solutions) if solutions is not None else 0
    LOGGER.info(f"Found {n_solutions} solutions. Walltime: {time.time() - t:.2f}s")

    if solutions is not None:
        if search_inverse:
            solutions = [f"({solution})" for solution in solutions]
        return sorted([MoveSequence(solution) for solution in solutions], key=len)
    return None
