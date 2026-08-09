from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from spruce.types import MoveSymbol
    from spruce.types import PermutationArray


def expanded_to_available_permutations(
    permutation: PermutationArray,
    available_permutations: dict[MoveSymbol, PermutationArray],
) -> dict[MoveSymbol, PermutationArray]:
    """Expand a permutation by matching repeated powers to known actions."""
    identity_bytes = np.arange(permutation.size, dtype=permutation.dtype).tobytes()
    symbol_by_perm_bytes = {perm.tobytes(): name for name, perm in available_permutations.items()}
    expanded_actions: dict[MoveSymbol, PermutationArray] = {}
    current_permutation = permutation

    while True:
        current_permutation = current_permutation.take(permutation)
        current_bytes = current_permutation.tobytes()
        if current_bytes == identity_bytes:
            break
        symbol = symbol_by_perm_bytes.get(current_bytes)
        if symbol is None:
            break
        expanded_actions[symbol] = available_permutations[symbol]

    return expanded_actions
