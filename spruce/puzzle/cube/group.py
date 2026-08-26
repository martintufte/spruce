"""Building the move group of a cube puzzle from its geometry and notation."""

from __future__ import annotations

import re
from functools import lru_cache
from typing import Final

from spruce.algebra.group import MoveMeta
from spruce.algebra.group import PermutationClassification
from spruce.configuration.regex import IDENTITY_SEARCH
from spruce.configuration.regex import ROTATION_SEARCH
from spruce.configuration.regex import SLICE_SEARCH
from spruce.configuration.regex import WIDE_SEARCH
from spruce.configuration.regex import canonical_key
from spruce.puzzle.cube.geometry import create_permutations
from spruce.puzzle.cube.notation import substitute_slice_move
from spruce.puzzle.cube.notation import substitute_wide_move
from spruce.puzzle.cube.rotations import canonicalize_rotations
from spruce.puzzle.cube.spec import Puzzle
from spruce.types import MoveSymbol

DEFAULT_GENERATOR_BY_PUZZLE: Final[dict[Puzzle, tuple[str, ...]]] = {
    Puzzle._2x2x2: ("U", "R", "F"),
    Puzzle._3x3x3: ("U", "D", "L", "R", "F", "B"),
    Puzzle._4x4x4: ("U", "Uw", "D", "L", "R", "Rw", "F", "Fw", "B"),
}


def cube_sort_key(symbol: MoveSymbol) -> tuple[int, ...]:
    """Rank a symbol by cube notation, falling back to its characters."""
    try:
        return (0, *canonical_key(symbol))
    except ValueError:
        return (1, *(ord(char) for char in symbol))


@lru_cache(maxsize=10)
def build_move_meta(puzzle: Puzzle) -> MoveMeta:
    """Build the move group for a cube puzzle from its geometry and notation."""
    cube_size = puzzle.cube_size
    permutations = create_permutations(cube_size=cube_size)

    # Classify the permutations and add substitutions
    classifications: dict[MoveSymbol, PermutationClassification] = {}
    substitutions: dict[MoveSymbol, tuple[MoveSymbol, ...]] = {}
    for symbol in permutations:
        if re.search(IDENTITY_SEARCH, symbol) is not None:
            classifications[symbol] = PermutationClassification.IDENTITY

        elif re.search(ROTATION_SEARCH, symbol) is not None:
            classifications[symbol] = PermutationClassification.ROTATION

        elif re.search(SLICE_SEARCH, symbol) is not None:
            classifications[symbol] = PermutationClassification.BASE
            substituted = substitute_slice_move(symbol)
            if substituted != (symbol,):
                substitutions[symbol] = substituted

        elif re.search(WIDE_SEARCH, symbol) is not None:
            classifications[symbol] = PermutationClassification.BASE
            substituted = substitute_wide_move(symbol, cube_size=cube_size)
            if substituted != (symbol,):
                substitutions[symbol] = substituted

        else:
            classifications[symbol] = PermutationClassification.BASE

    default = DEFAULT_GENERATOR_BY_PUZZLE.get(puzzle)
    default_generator_symbols = (
        None if default is None else frozenset(MoveSymbol(symbol) for symbol in default)
    )

    return MoveMeta.from_permutations(
        permutations=permutations,
        classifications=classifications,
        substitutions=substitutions,
        name=f"puzzle {puzzle.value}",
        sort_key=cube_sort_key,
        default_generator_symbols=default_generator_symbols,
        rotation_canonicalizer=canonicalize_rotations,
    )
