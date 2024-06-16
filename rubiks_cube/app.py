from typing import Any

import streamlit as st
import extra_streamlit_components as stx

from rubiks_cube.permutation import get_state
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
from rubiks_cube.utils.parser import parse_user_input


st.set_page_config(
    page_title="Fewest Moves Solver",
    page_icon="rubiks_cube/data/resources/favicon.png",
    layout="centered",
)


@st.cache_resource(experimental_allow_widgets=True)
def get_cookie_manager():
    return stx.CookieManager()


COOKIE_MANAGER = get_cookie_manager()
DEFAULT_SESSION: dict[str, Any] = {
    "scramble": MoveSequence(COOKIE_MANAGER.get("stored_scramble") or ""),
    "user": parse_user_input(COOKIE_MANAGER.get("stored_user") or ""),
}

for key, default in DEFAULT_SESSION.items():
    if key not in st.session_state:
        setattr(st.session_state, key, default)


def tag_state(
    starting_state,
    sequence: MoveSequence,
    inverse_sequence: MoveSequence
) -> str:
    """Tag the state of the cube."""
    combined_state = get_state(
        sequence=sequence,
        inverse_sequence=inverse_sequence,
        starting_state=starting_state,
        orientate_after=True,
    )
    return autotag_state(combined_state, default_tag="draft")


def main() -> None:
    """Render the main page."""

    st.subheader("Fewest Moves Solver")

    scramble_input = st.text_input(
        label="Scramble",
        value=COOKIE_MANAGER.get(cookie="stored_scramble"),
        placeholder="R' U' F ..."
    )
    if scramble_input is not None:
        scramble = remove_comment(scramble_input)
        if not is_valid_symbols(scramble):
            st.error("Invalid symbols in scramble")
            return
        formatted_scramble = format_string(scramble)
        scramble_moves = string_to_moves(formatted_scramble)
        if not is_valid_moves(scramble_moves):
            st.error("Invalid moves in scramble")
            return

        st.session_state.scramble = MoveSequence(scramble_moves)
        COOKIE_MANAGER.set(
            cookie="stored_scramble",
            val=scramble,
            key="stored_scramble"
        )

    scramble_state = get_state(st.session_state.scramble)

    fig = plot_cube_state(scramble_state)
    st.pyplot(fig, use_container_width=True)

    # User input handling:
    user_input = st.text_area(
        label="Moves",
        value=COOKIE_MANAGER.get(cookie="stored_user"),
        placeholder="Moves  // Comment\n...",
        height=160
    )
    if user_input is not None:
        st.session_state.user = parse_user_input(user_input)
        COOKIE_MANAGER.set(
            cookie="stored_user",
            val=user_input,
            key="stored_user"
        )

    normal, inverse = split_normal_inverse(st.session_state.user)
    tag = tag_state(
        sequence=normal,
        inverse_sequence=inverse,
        starting_state=scramble_state
    )
    if tag == "solved":
        progress = cleanup(unniss(st.session_state.user))
    else:
        progress = st.session_state.user

    out_string = f"{str(progress)}  // {tag} ({len(progress)})"
    st.text_input(label=tag, value=out_string, label_visibility="collapsed")

    col1, col2, _, = st.columns((1, 1, 3))
    premoves = col1.toggle(label="Premoves", key="col1", value=True)
    invert = col2.toggle(label="Invert", key="col2", value=False)

    if premoves:
        full_sequence = ~inverse + st.session_state.scramble + normal
    else:
        full_sequence = st.session_state.scramble + st.session_state.user
    full_sequence = ~unniss(full_sequence) if invert else unniss(full_sequence)

    fig_user = plot_cube_state(get_state(full_sequence))
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
