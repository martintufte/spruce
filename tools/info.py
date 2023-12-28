import streamlit as st
from utils.permutations import (
    blind_trace,
    block_trace,
    count_solved,
)


def render_info_settings():
    """Render the settings bar for Info."""
    col1, col2, col3, col4 = st.columns(4)
    draw_in_3D = col1.toggle(
        label="Draw 3D",
        value=False,
    )
    some_setting = col2.toggle(
        label="Blind trace",
        value=False,
    )
    another_setting = col3.toggle(
        label="Block trace",
        value=False,
    )
    last_setting = col4.toggle(
        label="\\# solved",
        value=False,
    )

    return draw_in_3D, some_setting, another_setting, last_setting


def render_info():
    """Info tool."""

    # Settings
    draw_in_3D, some_setting, \
        another_setting, last_setting = render_info_settings()

    # Permutation
    # full_sequence = st.session_state.scramble + st.session_state.user

    permutation = st.session_state.permutation
    # get_cube_permutation(full_sequence)

    if draw_in_3D:
        st.write("3D drawing is enabled!")
    if some_setting:
        blind_tr = blind_trace(permutation)
        st.write("#### " + blind_tr)
    if another_setting:
        block_tr = block_trace(permutation)
        st.write("#### " + block_tr)
    if last_setting:
        solved = count_solved(permutation)
        st.write("#### Solved: " + str(solved))


class Info():
    """ Info class. """
    def __init__(self):
        self.name = "Insertion Finder"
        pass

    def render(self):
        render_info()

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name
