import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

from .rubiks_cube import get_cube_permutation, Sequence

COLORS = {
  "U": "#FFFFFF",
  "F": "#00d800",
  "R": "#e00000",
  "B": "#1450f0",
  "L": "#ff7200",
  "D": "#ffff00",
  "G": "#606060",
}


def get_cube_string(state: str = "solved") -> np.ndarray:
    """Get a cube state."""

    match state:
        case "solved":
            cube_string = "U"*9 + "F"*9 + "R"*9 + "B"*9 + "L"*9 + "D"*9
        case "F2L":
            cube_string = "G"*12 + "B"*6 + "G"*3 + "R"*6 + "G"*3 + \
                "F"*6 + "G"*3 + "L"*6 + "U"*9
        case "OLL":
            cube_string = "D"*9 + "G"*3 + "B"*6 + "G"*3 + "R"*6 + \
                "G"*3 + "F"*6 + "G"*3 + "L"*6 + "U"*9
        case "DR":
            cube_string = "D"*9 + "G"*36 + "D"*9
        case _:
            raise ValueError(f"Invalid cube state: {state}")

    cube_string = np.array(list(cube_string), dtype=np.str_)

    return cube_string


def plot_piece(ax, x, y, piece):
    """Draw a piece of the cube."""

    ax.add_patch(
      Rectangle(
        (x, y), 1, 1, edgecolor="black", facecolor=COLORS[piece])
    )


def plot_face(ax, piece_list, x_rel, y_rel, padding):
    """Draw a face of the cube."""

    for i, piece in enumerate(piece_list):
        x = x_rel + i % 3 * (1 + padding)
        y = y_rel + (2 - i // 3) * (1 + padding)

        plot_piece(ax, x, y, str(piece))


def plot_cube_state(seq: Sequence):
    """Draw a cube state."""

    cube_string = get_cube_string(state="solved")
    permutation = get_cube_permutation(seq)

    # Apply the permutation
    cube_string = cube_string[permutation]

    # Set the background color to transparent
    plt.rcParams.update({
        "savefig.facecolor": (0.5, 0.5, 0.5, 0.0),
    })

    # Set the figure padding
    x_pad = 3.0
    y_pad = 0.1
    padding = 0
    padding_face = 0.25
    side_length = 3 + 2*padding + padding_face

    # Create the figure
    fig, ax = plt.subplots()
    ax.set_xlim(-x_pad, x_pad + 12 + 8*padding + 3*padding_face)
    ax.set_ylim(-y_pad, y_pad + 9 + 6*padding + 2*padding_face)
    ax.set_aspect("equal")
    ax.axis("off")

    # Plot the cube faces
    plot_face(ax, cube_string[:9], side_length, 2*side_length, padding)
    plot_face(ax, cube_string[9:18], side_length, side_length, padding)
    plot_face(ax, cube_string[18:27], 2*side_length, side_length, padding)
    plot_face(ax, cube_string[27:36], 3*side_length, side_length, padding)
    plot_face(ax, cube_string[36:45], 0, side_length, padding)
    plot_face(ax, cube_string[45:], side_length, 0, padding)

    return fig
