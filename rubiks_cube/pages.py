import streamlit as st
import extra_streamlit_components as stx
# from annotated_text.util import get_annotated_html
# from annotated_text import parameters
# parameters.SHOW_LABEL_SEPARATOR = False
# parameters.PADDING = "0.25rem 0.4rem"
from streamlit.runtime.state import SessionStateProxy


from rubiks_cube.fewest_moves import FewestMovesAttempt
from rubiks_cube.graphics import plot_cubex
from rubiks_cube.graphics import plot_cube_state
from rubiks_cube.state import get_rubiks_cube_state
from rubiks_cube.utils.parsing import parse_user_input
from rubiks_cube.utils.parsing import parse_scramble
from rubiks_cube.state.tag.patterns import get_cubexes
from rubiks_cube.state.permutation import invert


def app(
    session: SessionStateProxy,
    cookie_manager: stx.CookieManager,
) -> None:
    """Render the main app."""

    # Update cookies to avoid visual bugs with input text areas
    _ = cookie_manager.get_all()

    st.subheader("Rubiks Cube Solver")

    scramble_input = st.text_input(
        label="Scramble",
        value=cookie_manager.get("scramble_input"),
        placeholder="R' U' F ..."
    )
    if scramble_input is not None:
        session.scramble = parse_scramble(scramble_input)
        cookie_manager.set(
            cookie="scramble_input",
            val=scramble_input,
            key="scramble_input"
        )

    scramble_state = get_rubiks_cube_state(sequence=session.scramble)

    if st.toggle(label="Invert", key="invert_scramble", value=False):
        fig_scramble_state = invert(scramble_state)
    else:
        fig_scramble_state = scramble_state
    fig = plot_cube_state(fig_scramble_state)
    st.pyplot(fig, use_container_width=True)

    # User input handling:
    user_input = st.text_area(
        label="Moves",
        value=cookie_manager.get("user_input"),
        placeholder="Moves  // Comment\n...",
        height=200
    )
    if user_input is not None:
        session.user = parse_user_input(user_input)
        cookie_manager.set(
            cookie="user_input",
            val=user_input,
            key="user_input"
        )

    user_state = get_rubiks_cube_state(
        sequence=session.user,
        initial_state=scramble_state,
    )

    if st.toggle(label="Invert", key="invert_user", value=False):
        fig_user_state = invert(user_state)
    else:
        fig_user_state = user_state
    fig_user = plot_cube_state(fig_user_state)
    st.pyplot(fig_user, use_container_width=True)

    attempt = FewestMovesAttempt.from_string(
        cookie_manager.get("scramble_input") or "",
        cookie_manager.get("user_input") or "",
    )
    attempt.tag_step()
    st.code(str(attempt), language=None)


def patterns(
    session: SessionStateProxy,
    cookie_manager: stx.CookieManager,
) -> None:

    scramble_state = get_rubiks_cube_state(sequence=session.scramble)

    user_state = get_rubiks_cube_state(
        sequence=session.user,
        initial_state=scramble_state,
    )

    st.subheader("Patterns")
    cubexes = get_cubexes()
    tag = st.selectbox(
        label=" ",
        options=cubexes.keys(),
        label_visibility="collapsed"
    )
    if tag is not None:
        cubex = cubexes[tag]
        st.write(tag, len(cubex), cubex.match(user_state))
        for pattern in cubex.patterns:
            fig_pattern = plot_cubex(pattern)
            st.pyplot(fig_pattern, use_container_width=True)

    # st.subheader("Annotated text")
    # st.markdown(
    #     get_annotated_html("B' (F2 R' F)  ", ("eo", ""), " (4/4)"),
    #     unsafe_allow_html=True,
    # )


def docs(
    session: SessionStateProxy,
    cookie_manager: stx.CookieManager,
) -> None:
    """This is where the documentation should go!"""

    st.header("Docs")
    st.markdown("Created by Martin Gudahl Tufte")
