import logging
from typing import Final

import numpy as np

from rubiks_cube.configuration import CUBE_SIZE
from rubiks_cube.configuration.type_definitions import CubePattern
from rubiks_cube.configuration.type_definitions import CubePermutation
from rubiks_cube.state.permutation import get_identity_permutation
from rubiks_cube.state.utils import infer_cube_size
from rubiks_cube.tag.cubex import Cubex
from rubiks_cube.tag.cubex import get_cubexes

LOGGER: Final = logging.getLogger(__name__)


def get_rubiks_cube_pattern(
    tag: str | None = None,
    permutation: CubePermutation | None = None,
    cube_size: int = CUBE_SIZE,
) -> CubePattern:
    """Get a matchable Rubik's cube pattern.

    Args:
        tag (str, optional): Tag to solve. Defaults to None.
        permutation (CubePermutation | None, optional): Permutation of the cube. Defaults to None.
        cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.
    """
    if permutation is not None:
        cube_size = infer_cube_size(permutation)

    if tag == "solved" or tag is None:
        pattern = get_solved_pattern(cube_size=cube_size)
    else:
        cubexes = get_cubexes(cube_size=cube_size)
        if tag not in cubexes:
            raise ValueError("Cannot create the pattern for the given tag and cube size.")
        cubex = cubexes[tag]
        if len(cubex.patterns) > 1:
            LOGGER.warning("Multiple patterns found for the tag. Using the first one.")
        pattern = create_pattern_from_cubex(cubex.patterns[0])

    if permutation is not None:
        pattern = pattern[permutation]

    return pattern


def get_solved_pattern(cube_size: int = CUBE_SIZE) -> CubePattern:
    """Get the default Rubik's cube pattern.

    Args:
        cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.

    Returns:
        CubePattern: The default Rubik's cube pattern.
    """

    assert 1 <= cube_size <= 10, "Size must be between 1 and 10."

    return np.arange(6 * cube_size**2, dtype=int) // cube_size**2


def create_pattern_from_cubex(cubex: Cubex) -> CubePattern:
    """Create a goal state from a pattern using the mask and orientations.

    Args:
        cubex (Cubex): Cube Expression.

    Returns:
        CubePattern: Pattern state.
    """

    pattern: CubePattern = get_identity_permutation(cube_size=cubex.size)

    if cubex.mask is not None:
        pattern[~cubex.mask] = max(pattern) + 1
    for orientation in cubex.orientations:
        pattern[orientation] = max(pattern) + 1

    # Reindex the goal state
    indexes = sorted(list(set(list(pattern))))
    for i, index in enumerate(indexes):
        pattern[pattern == index] = i

    return pattern
