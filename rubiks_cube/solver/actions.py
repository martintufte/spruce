from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from rubiks_cube.configuration import CUBE_SIZE
from rubiks_cube.representation import get_rubiks_cube_permutation
from rubiks_cube.representation.permutation import create_permutations

if TYPE_CHECKING:
    from rubiks_cube.configuration.types import CubePermutation
    from rubiks_cube.move.algorithm import MoveAlgorithm
    from rubiks_cube.move.generator import MoveGenerator


def get_actions(
    generator: MoveGenerator | None = None,
    algorithms: list[MoveAlgorithm] | None = None,
    expand_generator: bool = True,
    cube_size: int = CUBE_SIZE,
) -> dict[str, CubePermutation]:
    """Get the action space from the move generator and from the algorithms.

    Args:
        generator (MoveGenerator): Move generator.
        algorithms (list[MoveAlgorithm] | None): List of algorithms to include in the action space.
        expand_generator (bool): Expand the generator actions to include standard actions.
        cube_size (int): Size of the cube.

    Returns:
        dict[str, CubePermutation]: Action space.
    """
    actions: dict[str, CubePermutation] = {}

    # Standard permutations
    standard_actions = create_permutations(cube_size=cube_size)

    # Add generator actions
    if generator is not None:
        for sequence in generator:
            permutation = get_rubiks_cube_permutation(
                sequence=sequence,
                cube_size=cube_size,
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
                algorithm.cube_range[0] is None or algorithm.cube_range[0] <= cube_size
            ), f"Cube size {cube_size} is too small for algorithm {algorithm.name}!"
            assert (
                algorithm.cube_range[1] is None or algorithm.cube_range[1] >= cube_size
            ), f"Cube size {cube_size} is too large for algorithm {algorithm.name}!"
            actions[algorithm.name] = get_rubiks_cube_permutation(
                sequence=algorithm.sequence,
                cube_size=cube_size,
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
