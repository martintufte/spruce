from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from spruce.move.sequence import MoveSequence

if TYPE_CHECKING:
    from collections.abc import Iterator
    from collections.abc import Set as AbstractSet

    from spruce.algebra.group import MoveMeta
    from spruce.types import MoveSymbol


def scramble_generator(
    length: int,
    generator: AbstractSet[MoveSymbol],
    move_meta: MoveMeta,
    n_scrambles: int,
    rng: np.random.Generator | None = None,
) -> Iterator[MoveSequence]:
    """Generate a random scramble sequence."""
    if rng is None:
        rng = np.random.default_rng()

    # Actions come back from MoveMeta in canonical order
    actions = move_meta.get_actions(generator=generator, expand=True)
    identity = np.arange(next(iter(actions.values())).size, dtype=int)

    # TODO(martin): Use MoveMeta instead
    # Precompute canonical pairs
    inv_closed = {tuple(identity), *(tuple(p) for p in actions.values())}
    next_possible_symbols: dict[MoveSymbol, list[MoveSymbol]] = {}
    for i, p_i in actions.items():
        for j, p_j in actions.items():
            p_ji = tuple(p_j[p_i])
            is_canonical = not (p_ji in inv_closed or (i > j and p_ji == tuple(p_i[p_j])))
            if is_canonical:
                if i not in next_possible_symbols:
                    next_possible_symbols[i] = []
                next_possible_symbols[i].append(j)

    for _ in range(n_scrambles):
        scramble_word: list[MoveSymbol] = []

        for _ in range(length):
            if scramble_word:
                possible_symbols = next_possible_symbols.get(
                    scramble_word[-1], list(actions.keys())
                )
            else:
                possible_symbols = list(actions.keys())
            scramble_word.append(rng.choice(possible_symbols))

        yield MoveSequence(scramble_word)
