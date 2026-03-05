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
    """Get actions from the generator and the algorithms provided.

    Args:
        move_meta (MoveMeta): Meta information about moves.
        generator (MoveGenerator): Move generator.
        algorithms (list[MoveAlgorithm] | None): List of algorithms to include in the action space.
        expand_generator (bool): Expand the generator actions to include standard actions.

    Returns:
        dict[str, CubePermutation]: Action space.

    Raises:
        ValueError: Need at least a generator or algorithms to create actions.
    """
    if generator is None and algorithms is None:
        raise ValueError("Need at least a generator or algorithms to create actions.")

    actions: dict[str, CubePermutation] = {}

    # Add generator actions
    if generator is not None:
        for sequence in generator:
            permutation = get_rubiks_cube_permutation(
                sequence=sequence,
                move_meta=move_meta,
            )
            actions[str(sequence)] = permutation
            if expand_generator:
                expanded_actions = expanded_to_available_permutations(
                    permutation, available_permutations=move_meta.permutations
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


def expanded_to_available_permutations(
    permutation: CubePermutation,
    available_permutations: dict[str, CubePermutation],
) -> dict[str, CubePermutation]:
    """Expand the permutation to include other available permutations.

    Apply the permutation repeatedly and check if it matches any standard actions.
    Break when no new permutations are found.

    Args:
        permutation (CubePermutation): The permutation to expand.
        available_permutations (dict[str, CubePermutation]): Available permutations to use.

    Returns:
        dict[str, CubePermutation]: Expanded actions from the provided standard actions.
    """
    identity = np.arange(permutation.size)
    expanded_actions: dict[str, CubePermutation] = {}
    current_permutation = permutation

    # Keep permuting to discover new available permutations
    while True:
        current_permutation = current_permutation[permutation]
        if np.array_equal(current_permutation, identity):
            break
        for name, available_permutation in available_permutations.items():
            if np.array_equal(current_permutation, available_permutation):
                expanded_actions[name] = available_permutation
                break
        else:
            break

    return expanded_actions
