from __future__ import annotations

from typing import TYPE_CHECKING

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

if TYPE_CHECKING:
    from matplotlib.axes import Axes
    from matplotlib.figure import Figure

    from rubiks_cube.configuration.types import CubeColor


def plot_piece(ax: Axes, x: float, y: float, color: str) -> None:
    """Plot a single piece of the cube.

    Args:
        ax (Axes): Axes object.
        x (float): X-coordinate.
        y (float): Y-coordinate.
        color (str): Cubie color.
    """
    rect = Rectangle(
        xy=(x, y),
        width=1,
        height=1,
        edgecolor="black",
        facecolor=color,
        linewidth=0.5,
    )
    ax.add_patch(rect)


def plot_face(
    ax: Axes,
    colored_cube: CubeColor,
    cube_size: int,
    x_rel: float,
    y_rel: float,
    padding: float,
    start_idx: int | None = None,
    plot_text: bool = False,
) -> None:
    """Draw a face of the cube.

    Args:
        ax (Axes): Axes object.
        colored_cube (CubeColor): Array of colored pieces.
        cube_size (int, optional): Size of the cube.
        x_rel (float): Shift in x-direction.
        y_rel (float): Shift in y-direction.
        padding (float): Padding between the pieces.
        start_idx (int | None, optional): Start idx. Defaults to None.
        plot_text (bool, optional): Whether to plot text of the faces. Defaults to False.
    """
    for i, color in enumerate(colored_cube):
        x = x_rel + i % cube_size * (1 + padding)
        y = y_rel + (cube_size - 1 - i // cube_size) * (1 + padding)

        plot_piece(ax, x, y, color)
        if start_idx is not None and plot_text:
            ax.text(x + 0.5, y + 0.5, str(start_idx + i), ha="center", va="center")


def plot_colored_cube_2D(colored_cube: CubeColor, cube_size: int) -> Figure:
    """Plot a cube string.

    Args:
        colored_cube (CubeColor): Array of colored cubies.
        cube_size (int): Size of the cube.

    Returns:
        Figure: Figure object.
    """
    # Set alpha to zero for transparency
    plt.rcParams.update({"savefig.facecolor": (1.0, 1.0, 1.0, 0.0)})

    # Set the figure padding
    n2 = cube_size**2
    x_pad = 3.0
    y_pad = 0.1
    padding = 0.0
    padding_face = 0.2
    side_length = cube_size + (cube_size - 1) * padding + padding_face

    # Create the figure
    fig, ax = plt.subplots(figsize=(4, 6))
    ax.set_xlim(-x_pad, x_pad + side_length * 4 - padding_face)
    ax.set_ylim(-y_pad, y_pad + side_length * 3 - padding_face)
    ax.set_aspect("equal")
    ax.axis("off")

    # Up
    plot_face(
        ax=ax,
        colored_cube=colored_cube[:n2],
        cube_size=cube_size,
        x_rel=side_length,
        y_rel=2 * side_length,
        padding=padding,
        start_idx=0,
    )

    # Front
    plot_face(
        ax=ax,
        colored_cube=colored_cube[n2 : n2 * 2],
        cube_size=cube_size,
        x_rel=side_length,
        y_rel=side_length,
        padding=padding,
        start_idx=n2,
    )

    # Right
    plot_face(
        ax=ax,
        colored_cube=colored_cube[n2 * 2 : n2 * 3],
        cube_size=cube_size,
        x_rel=2 * side_length,
        y_rel=side_length,
        padding=padding,
        start_idx=n2 * 2,
    )

    # Back
    plot_face(
        ax=ax,
        colored_cube=colored_cube[n2 * 3 : n2 * 4],
        cube_size=cube_size,
        x_rel=3 * side_length,
        y_rel=side_length,
        padding=padding,
        start_idx=n2 * 3,
    )

    # Left
    plot_face(
        ax=ax,
        colored_cube=colored_cube[n2 * 4 : n2 * 5],
        cube_size=cube_size,
        x_rel=0,
        y_rel=side_length,
        padding=padding,
        start_idx=n2 * 4,
    )

    # Down
    plot_face(
        ax=ax,
        colored_cube=colored_cube[n2 * 5 :],
        cube_size=cube_size,
        x_rel=side_length,
        y_rel=0,
        padding=padding,
        start_idx=n2 * 5,
    )

    return fig
