from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from rubiks_cube.configuration.regex import canonical_key
from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.solver.actions import get_actions

if TYPE_CHECKING:
    from collections.abc import Iterator

    from rubiks_cube.move.generator import MoveGenerator


def scramble_generator(
    length: int,
    generator: MoveGenerator,
    cube_size: int,
    n_scrambles: int,
    rng: np.random.Generator | None = None,
) -> Iterator[MoveSequence]:
    """Generate a random scramble sequence."""
    if rng is None:
        rng = np.random.default_rng()

    # Get the actions space so it can use canonical ordering
    actions = get_actions(generator, expand_generator=True, cube_size=cube_size)
    actions = {name: actions[name] for name in sorted(actions.keys(), key=canonical_key)}
    identity = np.arange(next(iter(actions.values())).size, dtype=int)

    # Precompute canonical pairs
    inv_closed = {tuple(identity), *(tuple(p) for p in actions.values())}
    next_possible_moves: dict[str, list[str]] = {}
    for i, p_i in actions.items():
        for j, p_j in actions.items():
            p_ji = tuple(p_j[p_i])
            is_canonical = not (p_ji in inv_closed or (i > j and p_ji == tuple(p_i[p_j])))
            if is_canonical:
                if i not in next_possible_moves:
                    next_possible_moves[i] = []
                next_possible_moves[i].append(j)

    for _ in range(n_scrambles):
        scramble_moves: list[str] = []

        for _ in range(length):
            if scramble_moves:
                possible_moves = next_possible_moves.get(scramble_moves[-1], list(actions.keys()))
            else:
                possible_moves = list(actions.keys())

            scramble_moves.append(rng.choice(possible_moves))

        yield MoveSequence(scramble_moves)
