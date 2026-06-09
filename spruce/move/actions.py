from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from spruce.configuration.types import PermutationArray


def expanded_to_available_permutations(
    permutation: PermutationArray,
    available_permutations: dict[str, PermutationArray],
) -> dict[str, PermutationArray]:
    """Expand a permutation by matching repeated powers to known actions."""
    identity = np.arange(permutation.size)
    expanded_actions: dict[str, PermutationArray] = {}
    current_permutation = permutation

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
