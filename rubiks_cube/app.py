from typing import Any

import streamlit as st
import extra_streamlit_components as stx
from annotated_text.util import get_annotated_html
from annotated_text import parameters

from rubiks_cube.fewest_moves.attempt import FewestMovesAttempt
from rubiks_cube.graphics.plotting import plot_cube_state, plot_cubex
from rubiks_cube.state import get_rubiks_cube_state
from rubiks_cube.state.tag.patterns import get_cubexes
from rubiks_cube.utils.parsing import parse_user_input
from rubiks_cube.utils.parsing import parse_scramble


st.set_page_config(
    page_title="Fewest Moves Solver",
    page_icon="rubiks_cube/data/resources/favicon.png",
    layout="centered",
)


@st.cache_resource(experimental_allow_widgets=True)
def get_cookie_manager() -> stx.CookieManager:
    return stx.CookieManager()


COOKIE_MANAGER = get_cookie_manager()
DEFAULT_SESSION: dict[str, Any] = {
    "scramble": parse_scramble(COOKIE_MANAGER.get("scramble_input") or ""),
    "user": parse_user_input(COOKIE_MANAGER.get("user_input") or ""),
}

for key, default in DEFAULT_SESSION.items():
    if key not in st.session_state:
        setattr(st.session_state, key, default)

parameters.SHOW_LABEL_SEPARATOR = False
parameters.BORDER_RADIUS = "0.5rem"
parameters.PADDING = "0.25rem 0.4rem"


def main() -> None:
    """Render the main page."""

    # Update cookies to avoid visual bugs with input text areas
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

    scramble_state = get_rubiks_cube_state(sequence=st.session_state.scramble)

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

    invert_state = st.toggle(label="Invert", key="invert", value=False)

    user_state = get_rubiks_cube_state(
        sequence=st.session_state.user,
        initial_state=scramble_state,
        invert_state=invert_state,
    )
    fig_user = plot_cube_state(user_state)
    st.pyplot(fig_user, use_container_width=True)

    if st.checkbox(label="Automatic tagging", value=True):
        attempt = FewestMovesAttempt.from_string(
            scramble_input or "",
            user_input or "",
        )
        attempt.tag_step()
        st.write(attempt)

    # Test annotated
    if False:
        lines = [
            get_annotated_html("B' (F2 R' F)  ", ("eo", ""), " (4/4)"),
            get_annotated_html("(L')  ", ("drm", ""), " (1/5)"),
            get_annotated_html("R2 L2 F2 D' B2 D B2 U' R'  ", ("dr", ""), " (9/14)"),  # noqa: E501
            get_annotated_html("U F2 L2 U2 B2 R2 U'  ", ("htr", ""), " (7/21)"),  # noqa: E501
            get_annotated_html("B2 L2 D2 R2 D2 L2  ", ("solved", ""), " (6-1/21)")  # noqa: E501
        ]
        for line in lines:
            st.markdown(line, unsafe_allow_html=True)

    if st.checkbox(label="Show state patterns", value=False):
        cubexes = get_cubexes()
        tag = st.selectbox(label=" ", options=cubexes.keys(), label_visibility="collapsed")  # noqa: E501
        if tag is not None:
            cubex = cubexes[tag]
            st.write(tag, len(cubex), cubex.match(user_state))
            for pattern in cubex.patterns:
                fig_pattern = plot_cubex(pattern)
                st.pyplot(fig_pattern, use_container_width=True)


if __name__ == "__main__":
    main()
