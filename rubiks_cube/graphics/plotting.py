import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

from rubiks_cube.graphics import COLORS
from rubiks_cube.tag.patterns import CubePattern


def get_cube_string(state: str = "solved") -> np.ndarray:
    """Get a cube state."""

    if state == "solved":
        cube_string = "U" * 9 + "F" * 9 + "R" * 9 + "B" * 9 + "L" * 9 + "D" * 9
    elif state == "F2L":
        cube_string = (
            "G" * 12
            + "B" * 6
            + "G" * 3
            + "R" * 6
            + "G" * 3
            + "F" * 6
            + "G" * 3
            + "L" * 6
            + "U" * 9
        )
    elif state == "OLL":
        cube_string = (
            "D" * 9
            + "G" * 3
            + "B" * 6
            + "G" * 3
            + "R" * 6
            + "G" * 3
            + "F" * 6
            + "G" * 3
            + "L" * 6
            + "U" * 9
        )
    else:
        raise ValueError(f"Invalid cube state: {state}")

    return np.array(list(cube_string), dtype=np.str_)


def plot_piece(ax, x, y, piece) -> None:
    """Plot a single piece of the cube."""

    ax.add_patch(
        Rectangle((x, y), 1, 1, edgecolor="black", facecolor=COLORS[piece])
    )


def plot_face(ax, piece_list, x_rel, y_rel, padding):
    """Draw a face of the cube."""

    for i, piece in enumerate(piece_list):
        x = x_rel + i % 3 * (1 + padding)
        y = y_rel + (2 - i // 3) * (1 + padding)

        plot_piece(ax, x, y, str(piece))


def plot_cube_state(
    permutation: np.ndarray | None = None,
    initial_state: str | np.ndarray = "solved",
):
    """Draw a cube state."""

    if isinstance(initial_state, str):
        cube_string = get_cube_string(initial_state)
    else:
        cube_string = initial_state

    # Apply the permutation
    if permutation is not None:
        cube_string = cube_string[permutation]

    # Set the background color to transparent
    plt.rcParams.update(
        {
            "savefig.facecolor": (1.0, 1.0, 1.0, 0.0),
        }
    )

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

    cube_string = np.array(list("G"*54), dtype=np.str_)

    # Apply the mask
    cube_string[pattern.mask] = "U"

    # Apply the orientations
    for orientation, color in zip(pattern.orientations, "BFDL"*3):
        cube_string[orientation] = color

    # Apply the relative masks
    for relative_mask in pattern.relative_masks:
        cube_string[relative_mask] = "R"

    # Set the background color to transparent
    plt.rcParams.update(
        {
            "savefig.facecolor": (1.0, 1.0, 1.0, 0.0),
        }
    )

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
