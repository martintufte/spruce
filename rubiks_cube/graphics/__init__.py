import numpy as np

from rubiks_cube.configuration import CUBE_SIZE
from rubiks_cube.configuration.enumeration import Face
from rubiks_cube.configuration.type_definitions import CubePermutation
from rubiks_cube.configuration.type_definitions import CubeState
from rubiks_cube.state.pattern import get_rubiks_cube_pattern


def get_colored_rubiks_cube(
    tag: str = "solved",
    permutation: CubePermutation | None = None,
    cube_size: int = CUBE_SIZE,
) -> CubeState:
    """Get a cube state with its colors.

    Args:
        tag (str, optional): Tag to solve. Defaults to "solved".
        cube_permutation (CubePermutation, optional): Permutation of the cube. Defaults to None.
        cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.

    Returns:
        CubeState: Cube state with colors.
    """
    pattern = get_rubiks_cube_pattern(tag=tag, permutation=permutation, cube_size=cube_size)

    color_map = {
        -1: Face.empty,
        0: Face.up,
        1: Face.front,
        2: Face.right,
        3: Face.back,
        4: Face.left,
        5: Face.down,
    }

    colored_pattern = np.array([color_map.get(i, Face.empty) for i in pattern], dtype=Face)

    return colored_pattern
