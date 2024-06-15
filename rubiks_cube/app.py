from typing import Any

import streamlit as st

from rubiks_cube.permutation import SOLVED_STATE
from rubiks_cube.permutation import get_permutation
from rubiks_cube.graphics.plotting import plot_cube_state
from rubiks_cube.tag import autotag_state
from rubiks_cube.utils.formatter import format_string
from rubiks_cube.utils.formatter import is_valid_symbols
from rubiks_cube.utils.formatter import remove_comment
from rubiks_cube.utils.move import is_valid_moves
from rubiks_cube.utils.move import string_to_moves
from rubiks_cube.utils.sequence import MoveSequence
from rubiks_cube.utils.sequence import split_normal_inverse
from rubiks_cube.utils.sequence import unniss
from rubiks_cube.utils.sequence import cleanup

st.set_page_config(
    page_title="Fewest Moves Solver",
    page_icon="rubiks_cube/data/resources/favicon.png",
    layout="centered",
)

DEFAULT_SESSION: dict[str, Any] = {
    "scramble": MoveSequence(),
    "user": MoveSequence(),
    "permutation": SOLVED_STATE,
}

for key, default in DEFAULT_SESSION.items():
    if key not in st.session_state:
        setattr(st.session_state, key, default)


# TODO: Make this return a (Attempt / Workbench) object
def parse_user_input(user_input: str) -> list[str]:
    """
    Parse user input lines and return the move list:
    - Remove comments
    - Replace definitions provided by the user
    - Replace substitutions
    - Remove skip characters
    - Check for valid symbols
    - Check for valid moves
    - Combine all moves into a single list of moves
    """
    user_lines = []
    additional_chars = ""
    skip_chars = ","
    definition_symbol = "="
    sub_start = "["
    sub_end = "]"
    definitions = {}
    substitutions = []
    lines = user_input.strip().split("\n")
    n_lines = len(lines)

    for i, line_input in enumerate(reversed(lines)):
        line = remove_comment(line_input)
        if line.strip() == "":
            continue
        for definition, definition_moves in definitions.items():
            line = line.replace(definition, definition_moves)
        for char in skip_chars:
            line = line.replace(char, "")

        if definition_symbol in line:
            definition, definition_moves = line.split(definition_symbol)
            definition = definition.strip()
            definition_moves = definition_moves.strip()
            assert is_valid_moves(string_to_moves(definition_moves)), \
                "Definition moves are invalid!"
            if definition[0] == sub_start and definition[-1] == sub_end:
                substitutions.append(definition_moves)
                continue
            else:
                assert len(definition) == 1, \
                    "Definition must be a single character!"
                assert not is_valid_symbols(definition), \
                    "Definition must not be an inbuild symbol!"
                assert len(definition_moves) > 0, \
                    "Definition must have at least one move!"
                if not is_valid_symbols(definition_moves, additional_chars):
                    st.warning(f"Invalid symbols entered at line {n_lines-i}")
                    break
                definitions[definition] = definition_moves
                additional_chars += definition
                continue
        else:
            if sub_start in line and sub_end in line:
                start_idx = line.index(sub_start)
                end_idx = line.index(sub_end)
                to_replace = line[start_idx+1:end_idx]
                if not is_valid_moves(string_to_moves(to_replace)):
                    st.warning(f"Invalid rewrite at line {n_lines-i}")
                    break
                if substitutions:
                    line = line[:line.index(sub_start)] + \
                        substitutions.pop() + line[line.index(sub_end)+1:]
                else:
                    line = line.replace(sub_start, "").replace(sub_end, "")

        if not is_valid_symbols(line, additional_chars):
            st.warning(f"Invalid symbols entered at line {n_lines-i}")
            break
        line_moves = string_to_moves(format_string(line))
        if not is_valid_moves(line_moves):
            st.warning(f"Invalid moves entered at line {n_lines-i}")
            break
        else:
            user_lines.append(line_moves)

    return sum(reversed(user_lines), [])


def render_settings() -> None:
    """Render the settings bar."""
    col1, col2, _, = st.columns((1, 1, 3))
    st.session_state.premoves = col1.toggle(
        label="Premoves",
        value=True,
    )
    st.session_state.invert = col2.toggle(
        label="Invert",
        value=False,
    )


def tag_progress(normal: MoveSequence, inverse: MoveSequence) -> str:
    """
    Tag the progress of the cube.
    """
    combined_permutation = get_permutation(
        sequence=normal,
        inverse_sequence=inverse,
        starting_permutation=st.session_state.permutation,
        orientate_after=True,
    )

    return autotag_state(combined_permutation, default_tag="draft")


def main() -> None:
    """Render the main page."""

    st.title("Fewest Moves Solver")
    scramble_input = st.text_input("Scramble", placeholder="R' U' F ...")
    scramble = remove_comment(scramble_input)

    if scramble.strip() == "":
        st.session_state.scramble = MoveSequence()

    if not is_valid_symbols(scramble):
        st.error("Invalid symbols entered!")
        return

    scramble_moves = string_to_moves(format_string(scramble))
    if not is_valid_moves(scramble_moves):
        st.error("Invalid moves entered!")
        return

    st.session_state.scramble = MoveSequence(scramble_moves)
    st.session_state.permutation = get_permutation(st.session_state.scramble)

    fig = plot_cube_state(st.session_state.permutation)
    st.pyplot(fig, use_container_width=True)

    user_input = st.text_area("Moves", placeholder="Moves  // Comment\n...")

    if user_input.strip() == "":
        st.session_state.user = MoveSequence()
        return

    st.session_state.user = cleanup(MoveSequence(parse_user_input(user_input)))
    normal, inverse = split_normal_inverse(st.session_state.user)
    tag = tag_progress(normal, inverse)

    if tag == "solved":
        progress = cleanup(unniss(st.session_state.user))
    else:
        progress = st.session_state.user

    out_string = f"{str(progress)}  // {tag} ({len(progress)})"
    st.text_input(label=tag, value=out_string, label_visibility="collapsed")

    render_settings()

    if st.session_state.premoves:
        full_sequence = ~inverse + st.session_state.scramble + normal
    else:
        full_sequence = st.session_state.scramble + st.session_state.user

    full_sequence = unniss(full_sequence)
    if st.session_state.invert:
        full_sequence = ~full_sequence

    fig_user = plot_cube_state(get_permutation(full_sequence))
    st.pyplot(fig_user, use_container_width=True)

    if False:
        from rubiks_cube.graphics.plotting import plot_cubex
        from rubiks_cube.tag.patterns import get_cubexes

        cubexes = get_cubexes()
        cubex = cubexes[tag]

        for pattern in cubex.patterns:
            fig_cubex = plot_cubex(pattern)
            st.pyplot(fig_cubex, use_container_width=True)

        for tag, cubex in cubexes.items():
            st.write(
                tag,
                f"({len(cubex.patterns)})",
                cubex.match(full_sequence),
                "score:", max(
                    sum(pattern.mask) +
                    max([
                        0,
                        sum([
                            sum(orientation * ~pattern.mask)
                            for orientation in pattern.orientations
                        ])
                    ]) +
                    max([
                        0,
                        sum([
                            sum(orientation)
                            for orientation in pattern.relative_masks
                        ])
                    ])
                    for pattern in cubex.patterns
                )
            )


if __name__ == "__main__":
    main()
