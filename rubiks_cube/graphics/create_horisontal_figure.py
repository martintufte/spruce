from typing import Final

import typer
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import numpy as np

from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.graphics import get_cube_string
from rubiks_cube.state import get_rubiks_cube_state
from rubiks_cube.configuration import COLOR_SCHEME


from rubiks_cube.state.tag.patterns import CubePattern
from rubiks_cube.configuration import CUBE_SIZE
from rubiks_cube.utils.enumerations import Pattern


app: Final = typer.Typer()


def plot_piece(ax, x, y, face) -> None:
    """Plot a single piece of the cube."""

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


def plot_face(ax, piece_list, x_rel, y_rel, padding, start_idx=None) -> None:
    """Draw a face of the cube."""

    for i, piece in enumerate(piece_list):
        x = x_rel + i % CUBE_SIZE * (1 + padding)
        y = y_rel + (CUBE_SIZE - 1 - i // CUBE_SIZE) * (1 + padding)

        plot_piece(ax, x, y, piece)
        if start_idx is not None:
            ax.text(
                x + 0.5, y + 0.5,
                str(start_idx + i),
                ha="center",
                va="center"
            )


def plot_cube_string2D(cube_string: np.ndarray):
    """Plot a cube string."""
    # Set the background color to transparent
    plt.rcParams.update({"savefig.facecolor": (1.0, 1.0, 1.0, 0.0)})

    # Set the figure padding
    n2 = CUBE_SIZE ** 2
    x_pad = 0.1
    y_pad = 0.1
    padding = 0.0
    padding_face = 0.2
    side_length = CUBE_SIZE + (CUBE_SIZE - 1) * padding + padding_face

    # Create the figure
    fig, ax = plt.subplots(figsize=(4, 3))
    ax.set_xlim(-x_pad, x_pad + side_length * 4 - padding_face)
    ax.set_ylim(-y_pad, y_pad + side_length * 3 - padding_face)
    ax.set_aspect("equal")
    # ax.grid(True, which="both", linestyle="--", linewidth=0.5, color="black")
    ax.axis("off")

    # Plot the cube faces
    plot_face(ax, cube_string[:n2], side_length, 2 * side_length, padding, 0)
    plot_face(ax, cube_string[n2:n2*2], side_length, side_length, padding, n2)
    plot_face(ax, cube_string[n2*2:n2*3], 2*side_length, side_length, padding, n2*2)  # noqa E501
    plot_face(ax, cube_string[n2*3:n2*4], 3*side_length, side_length, padding, n2*3)  # noqa E501
    plot_face(ax, cube_string[n2*4:n2*5], 0, side_length, padding, n2*4)
    plot_face(ax, cube_string[n2*5:], side_length, 0, padding, n2*5)

    return fig


def plot_cube_state(permutation: np.ndarray | None = None):
    """Draw a cube state."""

    cube_string = get_cube_string(permutation)

    return plot_cube_string2D(cube_string)


def plot_cubex(pattern: CubePattern):
    """Draw a cubex pattern."""

    cube_string = np.array([Pattern.empty] * 6 * CUBE_SIZE ** 2, dtype=Pattern)
    for orientation in pattern.orientations:
        cube_string[orientation] = Pattern.orientation
    for relative_mask in pattern.relative_masks:
        cube_string[relative_mask] = Pattern.relative_mask
    cube_string[pattern.mask] = Pattern.mask

    return plot_cube_string2D(cube_string)


@app.command()
def create_figure(
    sequence: str = typer.Option(" "),
    file_name: str = typer.Option("figure.svg"),
    output_path: str = typer.Option("rubiks_cube/data/figures"),
) -> None:
    """Create an SVG icon of the Rubiks Cube State."""

    state = get_rubiks_cube_state(MoveSequence(sequence))
    cube_string = get_cube_string(state)

    # Create the SVG file
    figure = plot_cube_string2D(cube_string)

    # Save the figure
    output_dir = Path(output_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    figure.savefig(output_dir / file_name, bbox_inches='tight', format="svg")


if __name__ == "__main__":
    app()
