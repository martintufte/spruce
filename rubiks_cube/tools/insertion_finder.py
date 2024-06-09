import streamlit as st

from rubiks_cube.utils.sequence import count_length
from rubiks_cube.utils.sequence import Sequence


def execute_if(command):
    """Execute a Insertion Finder command."""
    if_command = f"if {command}"

    return if_command


def render_if_settings():
    """Render the settings bar for Insertion Finder."""
    col1, col2, col3, col4 = st.columns(4)
    keep_progress = col1.selectbox(
        "Can break progress",
        options=["Yes", "No"],
        index=0,
    )
    check = col2.selectbox(
        "Check",
        options=["Normal", "Normal or Inverse", "Combination"],
        index=1,
    )
    axis = col3.selectbox(
        "Axis",
        options=["All", "F/B", "R/L", "U/D"],
        index=0,
    )
    execute = col4.button(
        label="Execute"
    )
    return keep_progress, check, axis, execute


def render_insertion_finder():
    """Insertion Finder tool."""

    # Settings
    keep_progress, check, axis, execute = render_if_settings()

    if execute:
        with st.spinner("Looking for shortned sequence..."):
            moves = st.session_state.user.moves

            output = execute_if(
                f"insert {keep_progress} {check} {axis} {moves}"
            )

            output = output.split("\n")

            # Parse output
            solutions = []
            for line in output:
                if line.startswith("Solution"):
                    solutions.append(line.split(": ")[1])

            # Render output
            st.write(f"Found {len(solutions)} solutions:")
            for solution in solutions:
                st.write(Sequence(solution))
            st.write(f"Number of solutions: {len(solutions)}")
            if len(solutions) > 0:
                st.write(f"Number of moves: {count_length(solutions[0])}")

            # Save solutions
            # st.session_state.solutions = solutions
            # st.session_state.solution_index = 0


class InsertionFinder():
    """ Nissy class. """
    def __init__(self):
        self.name = "Insertion Finder"
        pass

    def render(self):
        render_insertion_finder()

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name
