from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from rubiks_cube.representation import get_rubiks_cube_permutation

if TYPE_CHECKING:
    from rubiks_cube.configuration.types import CubePermutation
    from rubiks_cube.move.algorithm import MoveAlgorithm
    from rubiks_cube.move.generator import MoveGenerator
    from rubiks_cube.move.meta import MoveMeta


def get_actions(
    move_meta: MoveMeta,
    generator: MoveGenerator | None = None,
    algorithms: list[MoveAlgorithm] | None = None,
    expand_generator: bool = True,
) -> dict[str, CubePermutation]:
    """Get the action space from the move generator and from the algorithms.

    Args:
        move_meta (MoveMeta): Meta information about moves.
        generator (MoveGenerator): Move generator.
        algorithms (list[MoveAlgorithm] | None): List of algorithms to include in the action space.
        expand_generator (bool): Expand the generator actions to include standard actions.

    Returns:
        dict[str, CubePermutation]: Action space.
    """
    actions: dict[str, CubePermutation] = {}

    # Standard permutations
    standard_actions = move_meta.permutations

    # Add generator actions
    if generator is not None:
        for sequence in generator:
            permutation = get_rubiks_cube_permutation(
                sequence=sequence,
                move_meta=move_meta,
            )
            actions[str(sequence)] = permutation
            if expand_generator:
                expanded_actions = expanded_to_standard_actions(
                    permutation, standard_actions=standard_actions
                )
                actions.update(expanded_actions)

    # Add algorithm actions
    if algorithms is not None:
        for algorithm in algorithms:
            assert algorithm.name not in actions, f"Algorithm {algorithm.name} already in actions!"
            assert (
                algorithm.cube_range[0] is None or algorithm.cube_range[0] <= move_meta.cube_size
            ), f"Cube size {move_meta.cube_size} is too small for algorithm {algorithm.name}!"
            assert (
                algorithm.cube_range[1] is None or algorithm.cube_range[1] >= move_meta.cube_size
            ), f"Cube size {move_meta.cube_size} is too large for algorithm {algorithm.name}!"
            actions[algorithm.name] = get_rubiks_cube_permutation(
                sequence=algorithm.sequence,
                move_meta=move_meta,
            )

    return actions


def expanded_to_standard_actions(
    permutation: CubePermutation,
    standard_actions: dict[str, CubePermutation],
) -> dict[str, CubePermutation]:
    """Expand the permutation to include standard actions.

    Apply the permutation repeatedly and check if it matches any standard actions.
    Break when no new permutations are found.

    Args:
        permutation (CubePermutation): The permutation to expand.
        standard_actions (dict[str, CubePermutation]): Standard actions to use for expansion.

    Returns:
        dict[str, CubePermutation]: Expanded actions from the provided standard actions.
    """
    identity = np.arange(permutation.size)
    expanded_actions: dict[str, CubePermutation] = {}
    current_permutation = permutation[permutation]

    while True:
        if np.array_equal(current_permutation, identity):
            break
        for name, std_permutation in standard_actions.items():
            if np.array_equal(current_permutation, std_permutation):
                expanded_actions[name] = std_permutation
                break
        else:
            break
        current_permutation = current_permutation[permutation]

    return expanded_actions
