import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

from rubiks_cube.graphics import COLOR_SCHEME
from rubiks_cube.state.tag.patterns import CubePattern
from rubiks_cube.utils.enumerations import Face
from rubiks_cube.utils.enumerations import Pattern


def get_cube_string() -> np.ndarray:
    """Get a cube state."""

    initial_state = [Face.up] * 9 + [Face.front] * 9 + [Face.right] * 9 + \
        [Face.blue] * 9 + [Face.left] * 9 + [Face.down] * 9

    return np.array(initial_state, dtype=Face)


def plot_piece(ax, x, y, face) -> None:
    """Plot a single piece of the cube."""

    ax.add_patch(
        Rectangle(
            xy=(x, y),
            width=1,
            height=1,
            edgecolor="black",
            facecolor=COLOR_SCHEME[face]
        )
    )


def plot_face(ax, piece_list, x_rel, y_rel, padding):
    """Draw a face of the cube."""

    for i, piece in enumerate(piece_list):
        x = x_rel + i % 3 * (1 + padding)
        y = y_rel + (2 - i // 3) * (1 + padding)

        plot_piece(ax, x, y, piece)


def plot_cube_state(permutation: np.ndarray | None = None):
    """Draw a cube state."""

    cube_string = get_cube_string()

    if permutation is not None:
        cube_string = cube_string[permutation]

    # Set the background color to transparent
    plt.rcParams.update({"savefig.facecolor": (1.0, 1.0, 1.0, 0.0)})

    # Set the figure padding
    x_pad = 3.0
    y_pad = 0.1
    padding = 0.0
    padding_face = 0.0
    side_length = 3 + 2 * padding + padding_face

    # Create the figure
    fig, ax = plt.subplots()
    ax.set_xlim(-x_pad, x_pad + 12 + 8 * padding + 3 * padding_face)
    ax.set_ylim(-y_pad, y_pad + 9 + 6 * padding + 2 * padding_face)
    ax.set_aspect("equal")
    ax.axis("off")

    # Plot the cube faces
    plot_face(ax, cube_string[:9], side_length, 2 * side_length, padding)
    plot_face(ax, cube_string[9:18], side_length, side_length, padding)
    plot_face(ax, cube_string[18:27], 2 * side_length, side_length, padding)
    plot_face(ax, cube_string[27:36], 3 * side_length, side_length, padding)
    plot_face(ax, cube_string[36:45], 0, side_length, padding)
    plot_face(ax, cube_string[45:], side_length, 0, padding)

    return fig


def plot_cubex(pattern: CubePattern):
    """Draw a cubex pattern."""

    cube_string = np.array([Pattern.empty] * 54, dtype=Pattern)
    cube_string[pattern.mask] = Pattern.mask
    for relative_mask in pattern.relative_masks:
        cube_string[relative_mask] = Pattern.relative_mask
    for orientation in pattern.orientations:
        cube_string[orientation] = Pattern.orientation

    # Transparent background
    plt.rcParams.update({"savefig.facecolor": (1.0, 1.0, 1.0, 0.0)})

    # Set the figure padding
    x_pad = 3.0
    y_pad = 0.1
    padding = 0.0
    padding_face = 0.0
    side_length = 3 + 2 * padding + padding_face

    # Create the figure
    fig, ax = plt.subplots()
    ax.set_xlim(-x_pad, x_pad + 12 + 8 * padding + 3 * padding_face)
    ax.set_ylim(-y_pad, y_pad + 9 + 6 * padding + 2 * padding_face)
    ax.set_aspect("equal")
    ax.axis("off")

    # Plot the cube faces
    plot_face(ax, cube_string[:9], side_length, 2 * side_length, padding)
    plot_face(ax, cube_string[9:18], side_length, side_length, padding)
    plot_face(ax, cube_string[18:27], 2 * side_length, side_length, padding)
    plot_face(ax, cube_string[27:36], 3 * side_length, side_length, padding)
    plot_face(ax, cube_string[36:45], 0, side_length, padding)
    plot_face(ax, cube_string[45:], side_length, 0, padding)

    return fig
