import logging
from typing import Final

import extra_streamlit_components as stx
import numpy as np
import streamlit as st
from annotated_text import annotation
from annotated_text import parameters
from annotated_text.util import get_annotated_html
from streamlit.runtime.state import SessionStateProxy

from rubiks_cube.attempt import Attempt
from rubiks_cube.configuration import CUBE_SIZE
from rubiks_cube.configuration.enumeration import Metric
from rubiks_cube.configuration.enumeration import Piece
from rubiks_cube.configuration.enumeration import Status
from rubiks_cube.graphics import COLOR
from rubiks_cube.graphics.horisontal import plot_colored_cube_2D
from rubiks_cube.graphics.horisontal import plot_cube_state
from rubiks_cube.move.generator import MoveGenerator
from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.solver import solve_step
from rubiks_cube.state import get_rubiks_cube_state
from rubiks_cube.state.utils import invert
from rubiks_cube.tag.cubex import Cubex
from rubiks_cube.tag.cubex import get_cubexes
from rubiks_cube.utils.parsing import parse_scramble
from rubiks_cube.utils.parsing import parse_steps

LOGGER: Final = logging.getLogger(__name__)

parameters.PADDING = "0.25rem 0.4rem"
parameters.SHOW_LABEL_SEPARATOR = False


def app(session: SessionStateProxy, cookie_manager: stx.CookieManager, tool: str) -> None:
    """Render the Rubik's cube toolbox.

    Args:
        session (SessionStateProxy): Session state proxy.
        cookie_manager (stx.CookieManager): Cookie manager.
    """
    _ = cookie_manager.get_all()

    st.subheader(f"Rubik's Cube > {tool}")

    scramble_input = st.text_input(
        label="Scramble",
        value=cookie_manager.get("scramble_input"),
        placeholder="R' U' F ...",
    )
    if scramble_input is not None:
        session["scramble"] = parse_scramble(scramble_input)
        cookie_manager.set(cookie="scramble_input", val=scramble_input, key="scramble_input")

    scramble_permutation = get_rubiks_cube_state(sequence=session["scramble"])

    if st.toggle(label="Invert", key="invert_scramble_permutation", value=False):
        fig_scramble_permutation = invert(scramble_permutation)
    else:
        fig_scramble_permutation = scramble_permutation
    fig_scramble = plot_cube_state(permutation=fig_scramble_permutation)
    st.pyplot(fig_scramble, use_container_width=False)

    steps_input = st.text_area(
        label="Steps",
        value=cookie_manager.get("steps_input"),
        placeholder="Step  // Comment\n...",
        height=200,
    )
    if steps_input is not None:
        session["steps"] = parse_steps(steps_input)
        cookie_manager.set(cookie="steps_input", val=steps_input, key="steps_input")

    steps_combined = sum(session["steps"], start=MoveSequence())
    steps_permutation = get_rubiks_cube_state(
        sequence=steps_combined,
        initial_permutation=scramble_permutation,
    )

    if st.toggle(label="Invert", key="invert_steps_permutation", value=False):
        fig_steps_permutation = invert(steps_permutation)
    else:
        fig_steps_permutation = steps_permutation
    fig_steps = plot_cube_state(permutation=fig_steps_permutation)
    st.pyplot(fig_steps, use_container_width=False)


def autotagger(session: SessionStateProxy, cookie_manager: stx.CookieManager) -> None:
    """Render the autotagger.

    Args:
        session (SessionStateProxy): Session state proxy.
        cookie_manager (stx.CookieManager): Cookie manager.
    """

    app(session, cookie_manager, tool="Autotagger")

    st.subheader("Settings")
    metric = st.selectbox(
        label="Metric",
        index=1,
        options=[
            "Execution Turn Metric",
            "Half Turn Metric",
            "Slice Turn Metric",
            "Quarter Turn Metric",
        ],
        key="metric",
    )
    cols = st.columns([1, 1, 1, 1])
    with cols[0]:
        include_scramble = st.checkbox(label="Scramble", key="include_scramble", value=True)
    with cols[1]:
        include_steps = st.checkbox(label="Steps", key="include_steps", value=True)
    with cols[2]:
        include_final = st.checkbox(label="Final", key="include_final", value=True)
    with cols[3]:
        cleanup_final = st.checkbox(label="Cleanup final", key="cleanup", value=True)

    attempt = Attempt(
        scramble=session["scramble"],
        steps=session["steps"],
        metric=Metric(metric),
        include_scramble=include_scramble,
        include_steps=include_steps,
        include_final=include_final,
        cleanup_final=cleanup_final,
    )
    attempt.compile()
    st.code(str(attempt), language=None)


def solver(session: SessionStateProxy, cookie_manager: stx.CookieManager) -> None:
    """Render the solver.

    Args:
        session (SessionStateProxy): Session state proxy.
        cookie_manager (stx.CookieManager): Cookie manager.
    """

    app(session, cookie_manager, tool="Solver")

    cubexes = get_cubexes(cube_size=CUBE_SIZE)

    st.subheader("Settings")
    cols = st.columns([1, 1])
    with cols[0]:
        tag = st.selectbox(
            label="Tag",
            options=cubexes.keys(),
            key="tag",
        )
        subset = st.selectbox(
            label="Subset",
            options=cubexes[tag].names,
            key="subset",
        )
        n_solutions = st.number_input(
            label="Number of solutions",
            value=1,
            min_value=1,
            max_value=20,
            key="n_solutions",
        )
    with cols[1]:
        generator = st.text_input(
            label="Generator",
            value="<L, R, F, B, U, D>",
            key="generator",
        )
        max_search_depth = st.number_input(
            label="Max search depth",
            value=8,
            min_value=1,
            max_value=20,
            key="max_depth",
        )
        search_strategy = st.selectbox(
            label="Strategy",
            options=["Normal", "Inverse"],
            key="search_strategy",
        )

    if st.button("Solve", type="primary", use_container_width=True):
        with st.spinner("Finding solutions.."):
            solutions, search_summary = solve_step(
                sequence=sum((session["scramble"], *session["steps"]), start=MoveSequence()),
                generator=MoveGenerator(generator),
                algorithms=None,
                tag=tag,
                subset=subset,
                max_search_depth=max_search_depth,
                n_solutions=n_solutions,
                search_inverse=(search_strategy == "Inverse"),
            )
        if search_summary.status == Status.Success:
            if len(solutions) == 0:
                st.write(f"Tag '{tag}' is already solved!")
            else:
                st.write(
                    f"Found {len(solutions)}/{n_solutions} solution{'s' * (len(solutions) > 1)}:"
                )
                for solution in solutions:
                    st.markdown(
                        get_annotated_html(annotation(f"{solution}", "", background="#E6D8FD")),
                        unsafe_allow_html=True,
                    )
        elif search_summary.status == Status.Failure:
            st.write("Solver found no solutions!")


def pattern(session: SessionStateProxy, cookie_manager: stx.CookieManager) -> None:
    """Render the pattern page.

    Args:
        session (SessionStateProxy): Session state proxy.
        cookie_manager (stx.CookieManager): Cookie manager.
    """

    st.header("Patterns")

    cols = st.columns([1, 1])
    with cols[0]:
        cube_size = st.number_input(
            label="Cube size",
            value=3,
            min_value=2,
            max_value=10,
            key="size",
        )
        sequence = st.text_input(
            label="Mask of solved after sequence",
            value="",
            key="mask",
        )
    with cols[1]:
        generator = st.text_input(
            label="Generator",
            value="<L, R, F, B, U, D>",
            key="generator",
        )
        pieces = st.multiselect(
            label="Pieces",
            options=["corner", "edge", "center"],
            key="pieces",
        )
        create_pattern = st.button("Create Pattern", type="primary", use_container_width=True)

    if create_pattern:
        mask_sequence = MoveSequence(sequence) if sequence.strip() != "" else None

        piece_map: dict[str, Piece] = {
            "corner": Piece.corner,
            "edge": Piece.edge,
            "center": Piece.center,
        }

        cubex = Cubex.from_settings(
            name="Custom",
            solved_sequence=mask_sequence,
            pieces=[piece_map[p] for p in pieces],
            piece_orientations=MoveGenerator(generator),
            cube_size=cube_size,
        )

        st.write(cubex)
        pattern = cubex.patterns[0]
        color_map = {
            0: COLOR["gray"],
            1: COLOR["white"],
            2: COLOR["green"],
            3: COLOR["red"],
            4: COLOR["blue"],
            5: COLOR["orange"],
            6: COLOR["yellow"],
            7: COLOR["cyan"],
            8: COLOR["lime"],
            9: COLOR["purple"],
            10: COLOR["pink"],
            11: COLOR["beige"],
            12: COLOR["brown"],
            13: COLOR["indigo"],
            14: COLOR["tan"],
            15: COLOR["steelblue"],
            16: COLOR["olive"],
        }
        colored_cube = np.array([color_map.get(i, None) for i in pattern])
        st.pyplot(plot_colored_cube_2D(colored_cube), use_container_width=False)


def docs(session: SessionStateProxy, cookie_manager: stx.CookieManager) -> None:
    """Render the documentation.

    Args:
        session (SessionStateProxy): Session state proxy.
        cookie_manager (stx.CookieManager): Cookie manager.
    """

    st.header("Docs")
    st.markdown("This page is for documentation!")

    sequence = st.text_input(
        label="Sequence",
        value="R U R' U'",
        key="sequence",
    )

    st.markdown(
        get_annotated_html(annotation(f"{sequence}", "", background="#E6D8FD")),
        unsafe_allow_html=True,
    )
