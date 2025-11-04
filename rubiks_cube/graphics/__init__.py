from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING
from typing import Mapping

import numpy as np

from rubiks_cube.configuration import CUBE_SIZE
from rubiks_cube.configuration.enumeration import Goal

if TYPE_CHECKING:
    from rubiks_cube.configuration.types import CubeColor
    from rubiks_cube.configuration.types import CubePermutation

COLOR: Mapping[str, str] = MappingProxyType(
    {
        "gray": "#606060",
        "white": "#FFFFFF",
        "green": "#00d800",
        "red": "#e00000",
        "blue": "#1450f0",
        "orange": "#ff7200",
        "yellow": "#ffff00",
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

DEFAULT_COLOR_SCHEME: Mapping[int, str] = MappingProxyType(
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
    goal: Goal = Goal.solved,
    permutation: CubePermutation | None = None,
    color_scheme: Mapping[int, str] = DEFAULT_COLOR_SCHEME,
    cube_size: int = CUBE_SIZE,
) -> CubeColor:
    """Get a colored Rubik's cube from the permutation.

    Args:
        goal (Goal, optional): Goal to solve. Defaults to Goal.solved.
        permutation (CubePermutation, optional): Permutation of the cube. Defaults to None.
        color_scheme (Mapping[int, str], optional): Color scheme. Defaults to DEFAULT_COLOR_SCHEME.
        cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.

    Returns:
        CubeColor: Cube state with colors.

    Raises:
        NotImplementedError: Goal is not implemented.
    """
    if goal is Goal.solved:
        pattern = (np.arange(6 * cube_size**2, dtype=int) // cube_size**2).astype(int) + 1
    else:
        raise NotImplementedError(f"Goal '{goal}' is not implemented.")

    if permutation is not None:
        pattern = pattern[permutation]

    colored_cube = np.array([color_scheme.get(i, COLOR["gray"]) for i in pattern], dtype=str)

    return colored_cube
