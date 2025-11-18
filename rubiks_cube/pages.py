from __future__ import annotations

import contextlib
import logging
from typing import TYPE_CHECKING
from typing import Final

import streamlit as st
from annotated_text import annotation
from annotated_text import parameters
from annotated_text.util import get_annotated_html

from rubiks_cube.attempt import Attempt
from rubiks_cube.autotagger.cubex import get_cubexes
from rubiks_cube.configuration import CUBE_SIZE
from rubiks_cube.configuration import DEFAULT_GENERATOR
from rubiks_cube.configuration.enumeration import Goal
from rubiks_cube.configuration.enumeration import Metric
from rubiks_cube.configuration.enumeration import Status
from rubiks_cube.graphics.horizontal import plot_cube_state
from rubiks_cube.move.generator import MoveGenerator
from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.parsing import parse_scramble
from rubiks_cube.parsing import parse_steps
from rubiks_cube.representation import get_rubiks_cube_state
from rubiks_cube.representation.utils import invert
from rubiks_cube.solver import solve_pattern

if TYPE_CHECKING:
    import extra_streamlit_components as stx
    from streamlit.runtime.state import SessionStateProxy

LOGGER: Final = logging.getLogger(__name__)

parameters.PADDING = "0.25rem 0.4rem"  # ty: ignore[invalid-assignment]
parameters.SHOW_LABEL_SEPARATOR = False  # ty: ignore[invalid-assignment]


def app(session: SessionStateProxy, cookie_manager: stx.CookieManager, tool: str) -> dict[str, str]:
    """Render Spruce with the given tool.

    Args:
        session (SessionStateProxy): Session state proxy.
        cookie_manager (stx.CookieManager): Cookie manager.
        tool (str): Name of the tool.

    Returns:
        dict[str, str]: All cookies loaded from the cookie manager.
    """
    # Get all cookies to ensure they're loaded (only call this once)
    all_cookies = cookie_manager.get_all() or {}

    st.subheader(f"Spruce > {tool}")

    # Get current scramble value from cookie, with fallback
    current_scramble_value = all_cookies.get("scramble_input", "")

    scramble_input = st.text_input(
        label="Scramble",
        value=current_scramble_value,
        placeholder="R' U' F ...",
    )
    if scramble_input is not None:
        session["scramble"] = parse_scramble(scramble_input)
        # Try to set cookie, but don't fail if it doesn't work
        with contextlib.suppress(Exception):
            cookie_manager.set(cookie="scramble_input", val=scramble_input, key="scramble_input")

    scramble_permutation = get_rubiks_cube_state(sequence=session["scramble"])

    fig_scramble_permutation = (
        invert(scramble_permutation)
        if st.toggle(label="Invert", key="invert_scramble_permutation", value=False)
        else scramble_permutation
    )
    fig_scramble = plot_cube_state(permutation=fig_scramble_permutation)
    st.pyplot(fig_scramble, width="content")

    # Get current steps value from cookie, with fallback
    current_steps_value = all_cookies.get("steps_input", "")

    steps_input = st.text_area(
        label="Steps",
        value=current_steps_value,
        placeholder="Step  // Comment\n...",
        height=200,
    )
    if steps_input is not None:
        session["steps"] = parse_steps(steps_input)
        # Try to set cookie, but don't fail if it doesn't work
        with contextlib.suppress(Exception):
            cookie_manager.set(cookie="steps_input", val=steps_input, key="steps_input")

    steps_combined = sum(session["steps"], start=MoveSequence())
    steps_permutation = get_rubiks_cube_state(
        sequence=steps_combined,
        initial_permutation=scramble_permutation,
    )

    fig_steps_permutation = (
        invert(steps_permutation)
        if st.toggle(label="Invert", key="invert_steps_permutation", value=False)
        else steps_permutation
    )
    fig_steps = plot_cube_state(permutation=fig_steps_permutation)
    st.pyplot(fig_steps, width="content")

    return all_cookies


def autotagger(session: SessionStateProxy, cookie_manager: stx.CookieManager) -> None:
    """Render the autotagger.

    Args:
        session (SessionStateProxy): Session state proxy.
        cookie_manager (stx.CookieManager): Cookie manager.
    """
    _ = app(session, cookie_manager, tool="Autotagger")

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
    attempt = Attempt(
        scramble=session["scramble"],
        steps=session["steps"],
        metric=Metric(metric),
        cleanup_final=True,
    )
    scramble, steps, final = attempt.compile()

    lines = [scramble, steps, final]

    st.code("\n\n".join(lines), language=None)


def solver(session: SessionStateProxy, cookie_manager: stx.CookieManager) -> None:
    """Render the solver.

    Args:
        session (SessionStateProxy): Session state proxy.
        cookie_manager (stx.CookieManager): Cookie manager.
    """
    # Get cookies from app function to avoid duplicate get_all() calls
    all_cookies = app(session, cookie_manager, tool="Solver")

    # Initialize solutions in session state if not present
    if "solver_solutions" not in session:
        # Load previous solutions from cookies as initial state
        cached_solutions_str = all_cookies.get("solver_solutions", "")
        if cached_solutions_str:
            try:
                # Parse solutions from cookie (stored as newline-separated strings)
                session["solver_solutions"] = [
                    sol.strip() for sol in cached_solutions_str.split("\n") if sol.strip()
                ]
            except Exception:
                session["solver_solutions"] = []
        else:
            session["solver_solutions"] = []

    # Use session state as the source of truth
    cached_solutions = session["solver_solutions"]

    cubexes = get_cubexes(cube_size=CUBE_SIZE)

    st.subheader("Settings")
    cols = st.columns([1, 1])
    with cols[0]:
        goal = st.selectbox(
            label="Goal",
            options=[goal.value for goal in cubexes],
            key="pattern",
        )
        subset = st.selectbox(
            label="Subset",
            options=cubexes[Goal(goal)].names,
            key="subset",
        )
        n_solutions = st.number_input(
            label="Number of solutions",
            value=5,
            min_value=1,
            max_value=200,
            key="n_solutions",
        )
    with cols[1]:
        generator = st.text_input(
            label="Generator",
            value=DEFAULT_GENERATOR,
            key="generator",
        )
        max_search_depth = st.number_input(
            label="Max search depth",
            value=10,
            min_value=1,
            max_value=20,
            key="max_depth",
        )
        search_strategy = st.selectbox(
            label="Strategy",
            options=["Normal", "Inverse"],
            key="search_strategy",
        )

    # Add a clear solutions button
    col_solve, col_clear = st.columns([3, 1])

    with col_solve:
        solve_clicked = st.button("Solve", type="primary", width="stretch")
    with col_clear:
        clear_clicked = st.button("Clear", width="stretch")

    # Handle clear button
    if clear_clicked:
        session["solver_solutions"] = []
        cached_solutions = []
        try:
            cookie_manager.set(cookie="solver_solutions", val="", key="solver_solutions_clear")
        except Exception:
            st.warning("Could not clear solutions from cookies, but cleared from session")

    # Handle solve button
    if solve_clicked:
        with st.spinner("Finding solutions.."):
            solutions, search_summary = solve_pattern(
                sequence=sum((session["scramble"], *session["steps"]), start=MoveSequence()),
                generator=MoveGenerator(generator),
                algorithms=None,
                goal=Goal(goal),
                subset=subset,
                max_search_depth=max_search_depth,
                n_solutions=n_solutions,
                search_inverse=(search_strategy == "Inverse"),
            )
        if search_summary.status == Status.Success:
            if len(solutions) == 0:
                st.warning(f"Goal '{goal}' is already solved!")
            else:
                # Convert solutions to strings
                solution_strings = [str(solution) for solution in solutions]

                # Combine with cached solutions (avoid duplicates)
                all_solutions = cached_solutions.copy()
                for sol in solution_strings:
                    if sol not in all_solutions:
                        all_solutions.append(sol)

                # Update session state first (this is the source of truth)
                session["solver_solutions"] = all_solutions
                cached_solutions = all_solutions

                # Save to cookies for persistence
                try:
                    solutions_str = "\n".join(all_solutions)
                    cookie_manager.set(
                        cookie="solver_solutions", val=solutions_str, key="solver_solutions_save"
                    )
                except Exception:
                    pass  # Silently continue if cookie setting fails

        elif search_summary.status == Status.Failure:
            st.warning("Solver found no solutions!")

    # Display all solutions
    if cached_solutions:
        st.subheader(f"Solutions ({len(cached_solutions)} total)")
        for solution in cached_solutions:
            st.markdown(
                get_annotated_html(annotation(f"{solution}", "", background="#E6D8FD")),
                unsafe_allow_html=True,
            )


def beam_search(session: SessionStateProxy, cookie_manager: stx.CookieManager) -> None:
    """Render the beam search.

    Args:
        session (SessionStateProxy): Session state proxy.
        cookie_manager (stx.CookieManager): Cookie manager.
    """
    _ = app(session, cookie_manager, tool="Beam Search")

    st.subheader("Settings")

    # Get current JSON template from cookie, with fallback
    all_cookies = cookie_manager.get_all(key="beam search") or {}
    current_json_template = all_cookies.get(
        "json_template",
        """{
  "eo-fb": {
    "max_length": 7,
    "generator": "<L, R, F, B, U, D>",
    "normal": true,
    "inverse": true,
    "max_solutions": 100,
  },
  "dr-ud": {
    "max_length": 10,
    "generator": "<L, R, F2, B2, U, D>",
    "normal": true,
    "inverse": true,
    "max_solutions": 20,
  },
  "htr": {
    "max_length": 12,
    "generator": "<L2, R2, F2, B2, U, D>",
    "normal": true,
    "inverse": true,
    "max_solutions": 20,
  },
  "solved": {
    "max_length": 10,
    "generator": "<L2, R2, F2, B2, U2, D2>",
    "normal": true,
    "inverse": false,
    "max_solutions": 1,
  },
}""",
    )

    json_template = st.text_area(
        label="Template",
        value=current_json_template,
        placeholder='{\n  "eo-fb": {...}\n  ...\n}',
        height=200,
        key="json_template",
    )

    st.code(json_template, language="json")


def docs(session: SessionStateProxy, cookie_manager: stx.CookieManager) -> None:
    """Render the documentation.

    Args:
        session (SessionStateProxy): Session state proxy.
        cookie_manager (stx.CookieManager): Cookie manager.
    """
    st.header("Docs")
    st.markdown("Copyright © 2025 Martin Tufte")
