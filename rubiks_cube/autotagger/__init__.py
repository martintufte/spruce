from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from typing import Final

import numpy as np

from rubiks_cube.autotagger.cubex import get_cubexes
from rubiks_cube.autotagger.subset import distinguish_htr
from rubiks_cube.configuration import CUBE_SIZE
from rubiks_cube.configuration.enumeration import Goal
from rubiks_cube.representation.pattern import get_empty_pattern

if TYPE_CHECKING:
    from rubiks_cube.configuration.types import CubePattern
    from rubiks_cube.configuration.types import CubePermutation

LOGGER: Final = logging.getLogger(__name__)


def get_rubiks_cube_pattern(
    goal: Goal,
    subset: str | None = None,
    cube_size: int = CUBE_SIZE,
) -> CubePattern:
    """Get a matchable Rubik's cube pattern from the goal.

    Args:
        goal (Goal): Goal to solve.
        subset (str | None, optional): Subset of the pattern. Defaults to None.
        cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.
    """
    if goal is Goal.none:
        return get_empty_pattern(cube_size=cube_size)

    cubexes = get_cubexes(cube_size=cube_size)
    if goal not in cubexes:
        raise ValueError("Cannot create the pattern for the given pattern and cube size.")

    cubex = cubexes[goal]
    if subset is None:
        idx = 0
    elif subset in cubex.names:
        idx = cubex.names.index(subset)
    else:
        raise ValueError("Subset does not exist in the given pattern.")

    pattern = cubex.patterns[idx]

    return pattern


def autotag_permutation(
    permutation: CubePermutation,
    default: str = "none",
    cube_size: int = CUBE_SIZE,
) -> str:
    """Autotag the permutation.

    1. Find the pattern corresponding to the state.
    2. Post-process the pattern if necessary.

    Args:
        permutation (CubePermutation): Cube permutation.
        default (str, optional): Default pattern. Defaults to "none".
        cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.

    Returns:
        str: Goal of the state.
    """
    cubexes = get_cubexes(cube_size=cube_size)

    # Match pattern
    for pattern, cbx in cubexes.items():
        if cbx.match(permutation):
            return_tag = pattern.value
            break
    else:
        return_tag = default

    # Distinguish subsets
    if return_tag == "htr-like":
        return_tag = distinguish_htr(permutation)

    return return_tag


def autotag_step(
    initial_permutation: CubePermutation,
    final_permutation: CubePermutation,
    cube_size: int = CUBE_SIZE,
) -> str:
    """Goal the step.

    Args:
        initial_permutation (CubePermutation): Initial permutation.
        final_permutation (CubePermutation): Final permutation.
        cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.

    Returns:
        str: Goal of the step.
    """
    if np.array_equal(initial_permutation, final_permutation):
        return "rotation"

    initial_tag = autotag_permutation(initial_permutation, cube_size=cube_size)
    final_tag = autotag_permutation(final_permutation, cube_size=cube_size)

    step_dict = {
        "eo -> dr": "dr",
        "dr -> htr": "htr",
        "dr-fb -> htr": "htr",
        "dr-lr -> htr": "htr",
        "dr-ud -> htr": "htr",
        "dr -> fake-htr": "fake htr",
        "htr -> solved": "solved",
        "cross -> x-cross": "first pair",
        "x-cross -> xx-cross": "second pair",
        "x-cross -> xx-cross-adjacent": "second pair",
        "x-cross -> xx-cross-diagonal": "second pair",
        "x-cross -> xxx-cross": "second + third pair",
        "xx-cross -> xxx-cross": "third pair",
        "xx-cross-adjacent -> xxx-cross": "third pair",
        "xx-cross-diagonal -> xxx-cross": "third pair",
        "xx-cross-adjacent -> f2l+face": "last two pairs + oll",
        "xx-cross-diagonal -> f2l+face": "last two pairs + oll",
        "xx-cross -> f2l": "last pairs",
        "xxx-cross -> f2l": "fourth pair",
        "xxx-cross -> f2l+eo": "fourth pair + eo",
        "xxx-cross -> f2l+ep+co": "fourth pair + oll",
        "xxx-cross -> f2l+face": "fourth pair + oll",
        "f2l -> f2l+face": "oll",
        "f2l -> solved": "ll",
        "f2l+face -> solved": "pll",
        "f2l+eo -> f2l+face": "oll",
        "f2l+eo -> solved": "zbll",
        "f2l+ep+co -> solved": "pll",
    }

    step = f"{initial_tag} -> {final_tag}"
    if initial_tag == "none" and final_tag != "none":
        return final_tag

    elif initial_tag == final_tag:
        return "random moves"

    return step_dict.get(step, step)
