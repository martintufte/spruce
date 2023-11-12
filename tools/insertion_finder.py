import streamlit as st

# TODO: Add this!


def render_insertion_finder_buttons():
    """Render the action bar."""
    col1, col2, col3, col4 = st.columns(4)
    find_222 = col1.button(
        label="Insert corners"
    )
    find_223 = col2.button(
        label="Insert edges"
    )
    find_f2lm1 = col3.button(
        label="Find F2L-1"
    )
    find_ll = col4.button(
        label="Find LL"
    )
    return find_222, find_223, find_f2lm1, find_ll


def render_tool_insertion_finder():
    """ Insertion finder tool. """
    st.subheader("Insertion Finder")
    find_222, find_223, find_f2lm1, find_ll = render_insertion_finder_buttons()
