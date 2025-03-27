from types import MappingProxyType
from typing import Mapping

import numpy as np

from rubiks_cube.configuration import CUBE_SIZE
from rubiks_cube.configuration.types import CubePermutation
from rubiks_cube.configuration.types import CubeState
from rubiks_cube.tag import get_rubiks_cube_pattern

COLOR: Mapping[str, str] = MappingProxyType(
    {
        "white": "#FFFFFF",
        "green": "#00d800",
        "red": "#e00000",
        "blue": "#1450f0",
        "orange": "#ff7200",
        "yellow": "#ffff00",
        "gray": "#606060",
        "lime": "#B1ff16",
        "purple": "#cb00cb",
        "cyan": "#1ce8ff",
        "pink": "#ff0cD2",
        "beige": "#c8ad89",
        "brown": "#8e6200",
        "indigo": "#5c62d6",
        "tan": "#f5c26b",
        "steelblue": "#4682b4",
        "olive": "#808000",
    }
)

DEFAULT_COLOR_MAP: Mapping[int, str] = MappingProxyType(
    {
        0: COLOR["gray"],
        1: COLOR["white"],
        2: COLOR["green"],
        3: COLOR["red"],
        4: COLOR["blue"],
        5: COLOR["orange"],
        6: COLOR["yellow"],
    }
)


def get_colored_rubiks_cube(
    tag: str = "solved",
    permutation: CubePermutation | None = None,
    color_map: Mapping[int, str] = DEFAULT_COLOR_MAP,
    cube_size: int = CUBE_SIZE,
) -> CubeState:
    """Get a cube state with its colors.

    Args:
        tag (str, optional): Tag to solve. Defaults to "solved".
        permutation (CubePermutation, optional): Permutation of the cube. Defaults to None.
        color_map (Mapping[int, str], optional): Color map. Defaults to DEFAULT_COLOR_MAP.
        cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.

    Returns:
        CubeState: Cube state with colors.
    """
    if tag == "solved":
        pattern = (np.arange(6 * cube_size**2, dtype=int) // cube_size**2).astype(int) + 1
    else:
        pattern = get_rubiks_cube_pattern(tag=tag, cube_size=cube_size)

    if permutation is not None:
        pattern = pattern[permutation]

    colored_pattern = np.array([color_map.get(i, COLOR["gray"]) for i in pattern], dtype=str)

    return colored_pattern
