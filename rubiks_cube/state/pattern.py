import logging
from typing import Final

from rubiks_cube.configuration import CUBE_SIZE
from rubiks_cube.configuration.type_definitions import CubePattern
from rubiks_cube.state.permutation import get_identity_permutation
from rubiks_cube.tag.cubex import Cubex
from rubiks_cube.tag.cubex import get_cubexes

LOGGER: Final = logging.getLogger(__name__)


# TODO: This should replace get_colored_rubiks_cube in graphics/__init__.py
def get_rubiks_cube_pattern(tag: str | None = None, cube_size: int = CUBE_SIZE) -> CubePattern:
    """Setup the pattern and initial state.

    Args:
        tag (str, optional): Tag to solve. Defaults to None.
        cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.
    """
    if tag is not None and cube_size == 3:
        cubexes = get_cubexes(cube_size=cube_size)
        if tag not in cubexes:
            raise ValueError("Cannot find the step. Will not solve the step.")
        cubex = cubexes[tag].patterns[0]
        pattern = create_pattern_state(cubex)
    else:
        pattern = get_identity_permutation(cube_size=cube_size)

    return pattern


def create_pattern_state(cubex: Cubex) -> CubePattern:
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
