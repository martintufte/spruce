import hydralit_components as hc
import numpy as np
import streamlit as st

from rubiks_cube.tools import Info
from rubiks_cube.tools import InsertionFinder
from rubiks_cube.tools import SequenceShortner
from rubiks_cube.tools.nissy import Nissy
from rubiks_cube.tools.nissy import execute_nissy
from rubiks_cube.tools.nissy import generate_random_scramble
from rubiks_cube.utils.move import is_valid_moves
from rubiks_cube.utils.move import repr_moves
from rubiks_cube.utils.move import string_to_moves
from rubiks_cube.utils.sequence import Sequence
from rubiks_cube.utils.sequence import split_normal_inverse
from rubiks_cube.utils.formatter import format_string
from rubiks_cube.utils.formatter import is_valid_symbols
from rubiks_cube.utils.formatter import remove_comment
from rubiks_cube.permutation.initialize import get_permutation
from rubiks_cube.permutation.tracing import blind_trace
from rubiks_cube.graphics.plotting import plot_cube_state


st.set_page_config(
    page_title="Fewest Moves Solver",
    page_icon="data/favicon.png",
    layout="centered",
)


default_values = {
    "scramble": Sequence(),
    "user": Sequence(),
    "tool": Sequence(),
    "premoves": True,
    "invert": False,
    "tools": [
        Info(),
        Nissy(),
        InsertionFinder(),
        SequenceShortner(),
    ],
    "permutation": np.arange(54),
}

for key, default in default_values.items():
    if key not in st.session_state:
        setattr(st.session_state, key, default)


def parse_user_input(user_input: str) -> list[str]:
    """Parse user input and return the moves."""
    user_lines = []
    additional_chars = ""
    skip_chars = ","
    definition_symbol = "="
    definitions = {}
    lines = user_input.strip().split("\n")
    n_lines = len(lines)
    for i, line_input in enumerate(reversed(lines)):
        line = remove_comment(line_input)

        # Skip empty lines
        if line.strip() == "":
            continue

        # Replace definitions
        for definition, definition_moves in definitions.items():
            line = line.replace(definition, definition_moves)
        for char in skip_chars:
            line = line.replace(char, "")

        # Definition line
        if definition_symbol in line:
            definition, definition_moves = line.split(definition_symbol)
            assert len(definition.strip()) == 1, \
                "Definition must be a single character!"
            assert not is_valid_symbols(definition.strip()), \
                "Definition must not be an inbuild symbol!"
            assert len(definition_moves.strip()) > 0, \
                "Definition must have at least one move!"

            if not is_valid_symbols(definition_moves, additional_chars):
                st.warning("Invalid symbols entered at line " + str(n_lines-i))
                break
            definitions[definition.strip()] = definition_moves.strip()
            additional_chars += definition.strip()
            continue

        # Normal line
        else:
            if not is_valid_symbols(line, additional_chars):
                st.warning("Invalid symbols entered at line " + str(n_lines-i))
                break

            line_moves_str = format_string(line)
            line_moves = string_to_moves(line_moves_str)
            if not is_valid_moves(line_moves):
                st.warning("Invalid moves entered at line " + str(n_lines-i))
                break
            else:
                user_lines.append(line_moves)

    # Collect user moves from user lines
    user_moves = []
    for line in reversed(user_lines):
        user_moves += line

    return user_moves


def reset_session_state():
    """Reset the session state."""
    st.rerun()


# UNUSED
def render_generate_random_state():
    """Generate a random Rubiks cube state."""
    # Dropdown menu for cube size
    scramble_type = st.selectbox(
        label="Scramble type",
        label_visibility="collapsed",
        options=[
            "Generate random scramble:",
            "FMC",
            "EO",
            "DR",
            "HTR",
            "Edges",
            "Corners",
        ],
        index=0,
    )
    if scramble_type is None:
        scramble_type = "Choose scramble type"

    if scramble_type != "Choose scramble type":
        st.session_state.scramble = Sequence(
            generate_random_scramble(scramble_type.lower())
        )
        st.session_state.user = Sequence()
        st.session_state.tool = Sequence()
        reset_session_state()


def render_user_settings():
    """Render the settings bar."""

    col1, col2, _, _ = st.columns(4)
    st.session_state.premoves = col1.toggle(
        label="Use premoves",
        value=st.session_state.premoves,
    )
    st.session_state.invert = col2.toggle(
        label="Invert",
        value=st.session_state.invert,
    )


def render_main_page():
    """Render the main page."""

    # Title
    st.title("Fewest Moves Solver")

    # Scramble
    scramble_input = st.text_input("Scramble", placeholder="R' U' F ...")
    scramble = remove_comment(scramble_input)

    # Check if scramble is empty
    if scramble.strip() == "":
        st.session_state.scramble = Sequence()
        st.info("Enter a scramble to get started!")
        return

    # Check if scramble contains valid symbols
    if not is_valid_symbols(scramble):
        st.error("Invalid symbols entered!")
        return

    # Check if scramble contains valid moves
    scramble_moves_str = format_string(scramble)
    scramble_moves = string_to_moves(scramble_moves_str)
    if not is_valid_moves(scramble_moves):
        st.error("Invalid moves entered!")
        return

    # Set scramble
    st.session_state.scramble = Sequence(scramble_moves)

    # Draw scramble
    scramble_permutation = get_permutation(
        st.session_state.scramble,
        ignore_rotations=False,
    )
    st.session_state.permutation = scramble_permutation
    fig = plot_cube_state(scramble_permutation)
    st.pyplot(fig, use_container_width=True)

    # User moves
    user_input = st.text_area("Moves", placeholder="Moves // Comment\n...")

    # Check if user input is empty
    if user_input.strip() == "":
        st.session_state.user = Sequence()
        st.info("Enter some moves to get started or use the tools!")
        return

    # Set user moves
    user_moves = parse_user_input(user_input)
    st.session_state.user = Sequence(
        execute_nissy(f"cleanup {repr_moves(user_moves)}")
    )
    normal_moves, inverse_moves = split_normal_inverse(
        st.session_state.user
    )
    pre_moves = ~ inverse_moves

    # Clean up output
    out_string = str(st.session_state.user)
    out_string = execute_nissy(f"unniss {out_string}")
    out_string = execute_nissy(f"cleanup {out_string}")
    out_string = out_string.strip()
    n = len(out_string.split(" "))

    # Blind trace
    permutation = get_permutation(
        st.session_state.scramble +
        Sequence(out_string),
        ignore_rotations=True,
    )
    st.session_state.permutation = permutation

    trace = blind_trace(permutation)
    # TODO: Better definition of skeleton
    if len(trace) == 0:
        out_text = "Solved"
        out_comment = "Solved"
    elif len(trace) <= 6:
        out_text = "Skeleton"
        out_comment = trace
    else:
        out_text = "Draft"
        out_comment = ""
    if out_comment:
        out_comment += " "
    out_string = out_string + f"  // {out_comment}({n})"
    st.text_input(label=out_text, value=out_string)

    render_user_settings()

    if st.session_state.premoves:
        full_sequence = pre_moves + \
            st.session_state.scramble + \
            normal_moves
    else:
        full_sequence = st.session_state.scramble + \
            st.session_state.user

    full_sequence = Sequence(
        execute_nissy(f"unniss {full_sequence}")
    )
    if st.session_state.invert:
        full_sequence = ~ full_sequence

    # Draw draft
    full_sequence_permutation = get_permutation(
        full_sequence,
        ignore_rotations=False,
    )
    fig_user = plot_cube_state(full_sequence_permutation)
    st.pyplot(fig_user, use_container_width=True)


def render_tools():
    """Render the tools."""

    st.write("")

    option_tools = [
        {'icon': "fas fa-info-circle", 'label': "Info"},
        {'icon': "fas fa-hammer", 'label': "Block Builder"},
        {'icon': "fab fa-slack-hash", 'label': "Nissy"},
        {'icon': "fas fa-ruler-combined", 'label': "Insertion Finder"},
        {'icon': "fas fa-cut", 'label': "Sequence Shortner"},
        # {'icon': "fas fa-at", 'label': "Skeleton Finder"},
        # {'icon': "fas fa-th-large", 'label': "2x2"},
        # {'icon': "fas fa-th", 'label': "3x3"},
        # {'icon': "fas fa-file-download", 'label': "PDF creater"},
    ]

    over_theme = {
        'menu_background': '#F0F2F6',
        'txc_inactive': '#000000',
        'txc_active': '#FFFFFF',
        'option_active': '#FF4B4B',
    }
    tool = hc.option_bar(  # noqa: F841
        override_theme=over_theme,
        option_definition=option_tools,
    )

    # Tools
    match tool:
        case "Info":
            st.session_state.tools[0].render()
        case "Nissy":
            st.session_state.tools[1].render()
        case "Insertion Finder":
            st.session_state.tools[2].render()
        case "Sequence Shortner":
            st.session_state.tools[3].render()
        case _:
            st.info("Coming soon!")


if __name__ == "__main__":
    render_main_page()
    render_tools()
