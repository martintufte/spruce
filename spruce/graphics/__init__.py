from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

import numpy as np

from spruce.configuration.enumeration import Goal
from spruce.graphics.horizontal import plot_colored_cube_2d
from spruce.representation.pattern import get_solved_pattern

if TYPE_CHECKING:
    from collections.abc import Mapping

    from matplotlib.figure import Figure

    from spruce.configuration.types import PermutationArray
    from spruce.configuration.types import StringArray
    from spruce.move.meta import MoveMeta

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
    },
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
    },
)


def get_colored_rubiks_cube(
    permutation: PermutationArray,
    move_meta: MoveMeta,
    goal: Goal = Goal.solved,
) -> StringArray:
    """Get a colored Rubik's cube from the permutation.

    Args:
        permutation (PermutationArray, optional): Permutation of the cube.
        move_meta (MoveMeta): Meta information about moves.
        goal (Goal, optional): Goal to solve. Defaults to Goal.solved.

    Returns:
        StringArray: Cube state with colors.

    Raises:
        NotImplementedError: Goal is not implemented.
    """
    if goal is Goal.solved:
        pattern = get_solved_pattern(move_meta=move_meta)
    else:
        raise NotImplementedError(f"Goal '{goal}' is not implemented.")

    if permutation is not None:
        pattern = pattern[permutation]

    colored_cube = np.array([COLOR_SCHEME.get(i, COLOR["gray"]) for i in pattern], dtype=str)

    return colored_cube


def plot_permutation(permutation: PermutationArray, move_meta: MoveMeta) -> Figure:
    """Plot a colored cube permutation.

    Args:
        permutation (PermutationArray): Cube permutation.
        move_meta (MoveMeta): Meta information about moves.

    Returns:
        Figure: Figure object.
    """
    colored_cube = get_colored_rubiks_cube(permutation=permutation, move_meta=move_meta)

    cube_size = move_meta.cube_size
    return plot_colored_cube_2d(colored_cube, cube_size=cube_size)
