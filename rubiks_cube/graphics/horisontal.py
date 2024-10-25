import os
from pathlib import Path
from typing import Final

import matplotlib.pyplot as plt
import typer
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle

from rubiks_cube.configuration import COLOR_SCHEME
from rubiks_cube.configuration import CUBE_SIZE
from rubiks_cube.configuration.enumeration import Face
from rubiks_cube.configuration.path_definitions import DATA_DIR
from rubiks_cube.configuration.type_definitions import CubeState
from rubiks_cube.graphics import get_colored_rubiks_cube
from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.state import get_rubiks_cube_state

app: Final = typer.Typer()


def plot_piece(ax: Axes, x: float, y: float, face: Face) -> None:
    """Plot a single piece of the cube.

    Args:
        ax (Axes): Axes object.
        x (float): X-coordinate.
        y (float): Y-coordinate.
        face (Face): Face color.
    """

    ax.add_patch(
        Rectangle(
            xy=(x, y),
            width=1,
            height=1,
            edgecolor="black",
            facecolor=COLOR_SCHEME[face],
            linewidth=0.5,
        )
    )


def plot_face(
    ax: Axes,
    piece_list: CubeState,
    x_rel: float,
    y_rel: float,
    padding: float,
    start_idx: int | None = None,
    cube_size: int = CUBE_SIZE,
    plot_text: bool = False,
) -> None:
    """Draw a face of the cube.

    Args:
        ax (Axes): Axes object.
        piece_list (CubeState): List of pieces.
        x_rel (float): Shift in x-direction.
        y_rel (float): Shift in y-direction.
        padding (float): Padding between the pieces.
        start_idx (int | None, optional): Start idx. Defaults to None.
        cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.
        plot_text (bool, optional): Whether to plot text of the faces. Defaults to False.
    """

    for i, piece in enumerate(piece_list):
        x = x_rel + i % cube_size * (1 + padding)
        y = y_rel + (cube_size - 1 - i // cube_size) * (1 + padding)

        plot_piece(ax, x, y, piece)
        if start_idx is not None and plot_text:
            ax.text(x + 0.5, y + 0.5, str(start_idx + i), ha="center", va="center")


def plot_colored_cube_2D(
    colored_cube: CubeState,
    cube_size: int = CUBE_SIZE,
) -> Figure:
    """Plot a cube string.

    Args:
        colored_cube (CubeState): Cube string.
        cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.

    Returns:
        Figure: Figure object.
    """
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

    # Plot the cube faces
    plot_face(ax, colored_cube[:n2], side_length, 2 * side_length, padding, 0)
    plot_face(ax, colored_cube[n2 : n2 * 2], side_length, side_length, padding, n2)
    plot_face(ax, colored_cube[n2 * 2 : n2 * 3], 2 * side_length, side_length, padding, n2 * 2)
    plot_face(ax, colored_cube[n2 * 3 : n2 * 4], 3 * side_length, side_length, padding, n2 * 3)
    plot_face(ax, colored_cube[n2 * 4 : n2 * 5], 0, side_length, padding, n2 * 4)
    plot_face(ax, colored_cube[n2 * 5 :], side_length, 0, padding, n2 * 5)

    return fig


def plot_cube_state(cube_state: CubeState | None = None) -> Figure:
    """Plot a cube state.

    Args:
        cube_state (CubeState | None, optional): Cube state. Defaults to None.

    Returns:
        Figure: Figure object.
    """

    colored_cube = get_colored_rubiks_cube(cube_state)

    return plot_colored_cube_2D(colored_cube)


@app.command()
def create_figure(
    sequence: str = typer.Option(" "),
    file_name: str = typer.Option("figure.svg"),
    output_path: str = typer.Option(os.path.join(DATA_DIR, "figures")),
) -> None:
    """Create an SVG icon of the Rubiks Cube State.

    Args:
        sequence (str, optional): Move sequence. Defaults to " ".
        file_name (str, optional): File name. Defaults to "figure.svg".
        output_path (str, optional): Output path. Defaults to DATA_DIR / "figures".
    """

    state = get_rubiks_cube_state(MoveSequence(sequence))
    colored_cube = get_colored_rubiks_cube(state)

    # Create the SVG file
    figure = plot_colored_cube_2D(colored_cube)

    # Save the figure
    output_dir = Path(output_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    figure.savefig(output_dir / file_name, bbox_inches="tight", format="svg")


if __name__ == "__main__":
    app()
