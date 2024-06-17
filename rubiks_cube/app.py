from typing import Any

import streamlit as st
import extra_streamlit_components as stx
import numpy as np
from functools import reduce

from rubiks_cube.state import get_state
from rubiks_cube.graphics.plotting import plot_cube_state, plot_cubex
from rubiks_cube.tag import autotag_state
from rubiks_cube.tag.patterns import get_cubexes
from rubiks_cube.utils.sequence import MoveSequence
from rubiks_cube.utils.sequence import split_normal_inverse
from rubiks_cube.utils.sequence import unniss
from rubiks_cube.utils.sequence import cleanup
from rubiks_cube.utils.parsing import parse_user_input
from rubiks_cube.utils.parsing import parse_scramble


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
    "scramble": parse_scramble(COOKIE_MANAGER.get("scramble_input") or ""),
    "user": parse_user_input(COOKIE_MANAGER.get("user_input") or ""),
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

    # Update cookies to avoid visual bugs with input areas
    _ = COOKIE_MANAGER.get_all()

    st.subheader("Fewest Moves Solver")

    scramble_input = st.text_input(
        label="Scramble",
        value=COOKIE_MANAGER.get("scramble_input"),
        placeholder="R' U' F ..."
    )
    if scramble_input is not None:
        st.session_state.scramble = parse_scramble(scramble_input)
        COOKIE_MANAGER.set(
            cookie="scramble_input",
            val=scramble_input,
            key="scramble_input"
        )

    scramble_state = get_state(st.session_state.scramble)

    fig = plot_cube_state(scramble_state)
    st.pyplot(fig, use_container_width=True)

    # User input handling:
    user_input = st.text_area(
        label="Moves",
        value=COOKIE_MANAGER.get("user_input"),
        placeholder="Moves  // Comment\n...",
        height=160
    )
    if user_input is not None:
        st.session_state.user = parse_user_input(user_input)
        COOKIE_MANAGER.set(
            cookie="user_input",
            val=user_input,
            key="user_input"
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

    # Create mask of the cube
    from rubiks_cube.tag.patterns import Cubex
    user_pattern = Cubex.from_solved_after_sequence(full_sequence)

    st.subheader("Map of what is solved")
    for pattern in user_pattern.patterns:
        fig_pattern = plot_cubex(pattern)
        st.pyplot(fig_pattern, use_container_width=True)

    st.subheader("Cubex")
    cubexes = get_cubexes()
    tag = st.selectbox(label="Cubexes", options=cubexes.keys())
    if tag is not None:
        cubex = cubexes[tag]
        st.write(tag, len(cubex), cubex.match(full_sequence), max(
                sum(pattern.mask) +
                max([
                    0,
                    sum([
                        sum(orientation)
                        for orientation in pattern.orientations
                    ])
                ]) +
                max([
                    0,
                    np.sum(reduce(np.logical_or, pattern.relative_masks))
                    if pattern.relative_masks else 0
                ])
                for pattern in cubex.patterns
            ))
        for pattern in cubex.patterns:
            fig_pattern = plot_cubex(pattern)
            st.pyplot(fig_pattern, use_container_width=True)


if __name__ == "__main__":
    main()
