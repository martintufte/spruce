from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from spruce.representation import get_rubiks_cube_permutation

if TYPE_CHECKING:
    from spruce.configuration.types import PermutationArray
    from spruce.move.generator import MoveGenerator
    from spruce.move.meta import MoveMeta


def get_actions(
    move_meta: MoveMeta,
    generator: MoveGenerator,
    expand: bool = True,
) -> dict[str, PermutationArray]:
    """Get actions from the generator.

    Args:
        move_meta (MoveMeta): Meta information about moves.
        generator (MoveGenerator): Move generator.
        expand (bool): Expand the generator actions to include standard actions.

    Returns:
        dict[str, PermutationArray]: Action space.

    Raises:
        ValueError: Need a generator to create actions.
    """
    actions: dict[str, PermutationArray] = {}
    for sequence in generator:
        permutation = get_rubiks_cube_permutation(
            sequence=sequence,
            move_meta=move_meta,
        )
        actions[str(sequence)] = permutation
        if expand:
            expanded_actions = expanded_to_available_permutations(
                permutation,
                available_permutations=move_meta.permutations,
            )
            actions.update(expanded_actions)

    return actions


def expanded_to_available_permutations(
    permutation: PermutationArray,
    available_permutations: dict[str, PermutationArray],
) -> dict[str, PermutationArray]:
    """Expand the permutation to include other available permutations.

    Apply the permutation repeatedly and check if it matches any standard actions.
    Break when no new permutations are found.

    Args:
        permutation (PermutationArray): The permutation to expand.
        available_permutations (dict[str, PermutationArray]): Available permutations to use.

    Returns:
        dict[str, PermutationArray]: Expanded actions from the provided standard actions.
    """
    identity = np.arange(permutation.size)
    expanded_actions: dict[str, PermutationArray] = {}
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
