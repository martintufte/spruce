import logging
from typing import Final

from rubiks_cube.configuration import CUBE_SIZE
from rubiks_cube.configuration.type_definitions import CubeState
from rubiks_cube.state.permutation import get_identity_permutation
from rubiks_cube.tag.patterns import CubePattern
from rubiks_cube.tag.patterns import get_cubexes

LOGGER: Final = logging.getLogger(__name__)


def create_pattern_state(pattern: CubePattern) -> CubeState:
    """Create a goal state from a pattern using the mask and orientations.

    Args:
        pattern (CubePattern): Pattern state.

    Returns:
        CubeState: Pattern goal state.
    """

    goal_state = get_identity_permutation(cube_size=pattern.size)

    if pattern.mask is not None:
        goal_state[~pattern.mask] = max(goal_state) + 1
    for orientation in pattern.orientations:
        goal_state[orientation] = max(goal_state) + 1

    # Reindex the goal state
    indexes = sorted(list(set(list(goal_state))))
    for i, index in enumerate(indexes):
        goal_state[goal_state == index] = i

    return goal_state


def get_pattern_state(step: str | None = None, cube_size: int = CUBE_SIZE) -> CubeState:
    """Setup the pattern and initial state.

    Args:
        cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.
        step (str, optional): Step to solve. Defaults to None.
    """
    if step is not None and cube_size == 3:
        cubexes = get_cubexes(cube_size=cube_size)
        if step not in cubexes:
            raise ValueError("Cannot find the step. Will not solve the step.")
        cubex = cubexes[step].patterns[0]
        pattern = create_pattern_state(cubex)
    else:
        pattern = get_identity_permutation(cube_size=cube_size)

    return pattern
