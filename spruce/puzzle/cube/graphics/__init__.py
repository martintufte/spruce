from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

import numpy as np

from spruce.puzzle.cube.graphics.horizontal import plot_colored_cube_2d
from spruce.puzzle.cube.patterns import get_solved_pattern

if TYPE_CHECKING:
    from collections.abc import Mapping

    from matplotlib.figure import Figure

    from spruce.puzzle.cube.spec import Puzzle
    from spruce.types import PermutationArray
    from spruce.types import StringArray


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


def get_colored_puzzle(permutation: PermutationArray, puzzle: Puzzle) -> StringArray:
    """Get a solved colored puzzle using the permutation.

    Args:
        permutation (PermutationArray): Permutation of the puzzle.
        puzzle (Puzzle): Puzzle.

    Returns:
        StringArray: Puzzle state with colors.

    Raises:
        NotImplementedError: Goal is not implemented.
    """
    pattern = get_solved_pattern(puzzle=puzzle)

    if permutation is not None:
        pattern = pattern[permutation]

    colored_puzzle = np.array([COLOR_SCHEME.get(i, COLOR["gray"]) for i in pattern], dtype=str)

    return colored_puzzle


def plot_puzzle(permutation: PermutationArray, puzzle: Puzzle) -> Figure:
    """Plot the puzzle given the permutation.

    Args:
        permutation (PermutationArray): Permutation for puzzle.
        puzzle (Puzzle): Puzzle.

    Returns:
        Figure: Matplotlib figure object.
    """
    colored_puzzle = get_colored_puzzle(permutation=permutation, puzzle=puzzle)
    return plot_colored_cube_2d(colored_puzzle, cube_size=puzzle.cube_size)
