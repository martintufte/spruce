from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING
from typing import Mapping

import numpy as np

from rubiks_cube.configuration.enumeration import Goal
from rubiks_cube.graphics.horizontal import plot_colored_cube_2D
from rubiks_cube.representation.pattern import get_solved_pattern

if TYPE_CHECKING:
    from matplotlib.figure import Figure

    from rubiks_cube.configuration.types import PermutationArray
    from rubiks_cube.configuration.types import StringArray

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

COLOR_SCHEME: Mapping[int, str] = MappingProxyType(
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
    permutation: PermutationArray,
    cube_size: int,
    goal: Goal = Goal.solved,
) -> StringArray:
    """Get a colored Rubik's cube from the permutation.

    Args:
        permutation (PermutationArray, optional): Permutation of the cube. Defaults to None.
        cube_size (int): Size of the cube.
        goal (Goal, optional): Goal to solve. Defaults to Goal.solved.

    Returns:
        StringArray: Cube state with colors.

    Raises:
        NotImplementedError: Goal is not implemented.
    """
    if goal is Goal.solved:
        pattern = get_solved_pattern(cube_size=cube_size)
    else:
        raise NotImplementedError(f"Goal '{goal}' is not implemented.")

    if permutation is not None:
        pattern = pattern[permutation]

    colored_cube = np.array([COLOR_SCHEME.get(i, COLOR["gray"]) for i in pattern], dtype=str)

    return colored_cube


def plot_permutation(permutation: PermutationArray, cube_size: int) -> Figure:
    """Plot a colored cube permutation.

    Args:
        permutation (PermutationArray): Cube permutation.
        cube_size (int): Cube size.

    Returns:
        Figure: Figure object.
    """
    colored_cube = get_colored_rubiks_cube(permutation=permutation, cube_size=cube_size)

    return plot_colored_cube_2D(colored_cube, cube_size=cube_size)
