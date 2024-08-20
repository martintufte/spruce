import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

from rubiks_cube.configuration import COLOR_SCHEME
from rubiks_cube.state.tag.patterns import CubePattern
from rubiks_cube.configuration import CUBE_SIZE
from rubiks_cube.utils.enumerations import Face
from rubiks_cube.utils.enumerations import Pattern


def get_cube_string(state: np.ndarray | None = None) -> np.ndarray:
    """Get a cube state."""
    n2 = CUBE_SIZE ** 2
    initial_state = [Face.up] * n2 + [Face.front] * n2 + [Face.right] * n2 + \
        [Face.back] * n2 + [Face.left] * n2 + [Face.down] * n2

    state_str = np.array(initial_state, dtype=Face)

    if state is not None:
        state_str = state_str[state]

    return state_str


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


def plot_face(ax, piece_list, x_rel, y_rel, padding):
    """Draw a face of the cube."""

    for i, piece in enumerate(piece_list):
        x = x_rel + i % CUBE_SIZE * (1 + padding)
        y = y_rel + (CUBE_SIZE - 1 - i // CUBE_SIZE) * (1 + padding)

        plot_piece(ax, x, y, piece)


def plot_cube_string2D(cube_string: np.ndarray):
    """Plot a cube string."""
    # Set the background color to transparent
    plt.rcParams.update({"savefig.facecolor": (1.0, 1.0, 1.0, 0.0)})

    # Set the figure padding
    n2 = CUBE_SIZE ** 2
    x_pad = 3.0
    y_pad = 0.1
    padding = 0.0
    padding_face = 0.2
    side_length = CUBE_SIZE + (CUBE_SIZE - 1) * padding + padding_face

    # Create the figure
    fig, ax = plt.subplots(figsize=(4, 6))
    ax.set_xlim(-x_pad, x_pad + side_length * 4 + 3 * padding_face)
    ax.set_ylim(-y_pad, y_pad + side_length * 3 + 2 * padding_face)
    ax.set_aspect("equal")
    ax.axis("off")

    # Plot the cube faces
    plot_face(ax, cube_string[:n2], side_length, 2 * side_length, padding)
    plot_face(ax, cube_string[n2:n2*2], side_length, side_length, padding)
    plot_face(ax, cube_string[n2*2:n2*3], 2*side_length, side_length, padding)
    plot_face(ax, cube_string[n2*3:n2*4], 3*side_length, side_length, padding)
    plot_face(ax, cube_string[n2*4:n2*5], 0, side_length, padding)
    plot_face(ax, cube_string[n2*5:], side_length, 0, padding)

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


if False:
    import altair as alt
    import pandas as pd
    import streamlit as st

    # Sample data
    data = pd.DataFrame({
        'x': [1, 2, 3],
        'y': [4, 5, 6]
    })

    # Create a chart
    chart = alt.Chart(data).mark_line().encode(
        x='x',
        y='y'
    ).properties(
        width=300,
        height=200
    )

    # Display the chart in Streamlit
    st.altair_chart(chart)

    import plotly.graph_objects as go

    shape = {
        'type': 'rect',
        'x0': 0, 'y0': 0,
        'x1': 1, 'y1': 1,
        'line': {
            'color': 'rgba(128, 0, 128, 1)',
            'width': 2,
        },
        'fillcolor': 'rgba(128, 0, 128, 0.5)',
    }

    # Create the figure
    fig = go.Figure()

    # Add the rectangle to the figure
    fig.add_shape(shape)

    # Update the layout to remove axes
    fig.update_layout(
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        width=400,
        height=400,
        margin=dict(r=10, l=10, b=10, t=10)
    )

    # Display the plot in Streamlit without the mode bar
    st.plotly_chart(fig, use_container_width=True, config={
        'displayModeBar': False,
        'staticPlot': True
    })
