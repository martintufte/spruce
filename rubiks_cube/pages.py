from __future__ import annotations

import contextlib
import json
import logging
from typing import TYPE_CHECKING
from typing import Final

import streamlit as st
from annotated_text import parameters

from rubiks_cube.attempt import Attempt
from rubiks_cube.autotagger import autotag_permutation_with_subset
from rubiks_cube.autotagger.cubex import get_cubexes
from rubiks_cube.configuration import CUBE_SIZE
from rubiks_cube.configuration import DEFAULT_GENERATOR
from rubiks_cube.configuration import DEFAULT_METRIC
from rubiks_cube.configuration.enumeration import Goal
from rubiks_cube.configuration.enumeration import Status
from rubiks_cube.graphics.horizontal import plot_cube_state
from rubiks_cube.meta.move import MoveMeta
from rubiks_cube.move.generator import MoveGenerator
from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.move.sequence import cleanup
from rubiks_cube.move.sequence import measure
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

    st.subheader("Spruce 🌲")

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
    if "steps_input_pending" in st.session_state:
        st.session_state["steps_input"] = st.session_state.pop("steps_input_pending")
    if "steps_input" not in st.session_state:
        st.session_state["steps_input"] = current_steps_value

    st.text_area(
        label="Steps",
        value=st.session_state["steps_input"],
        placeholder="Step  // Comment\n...",
        height=200,
        key="steps_input",
    )
    steps_input = st.session_state.get("steps_input", "")
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

    toggle_cols = st.columns([1, 1, 1])
    with toggle_cols[0]:
        invert_steps = st.toggle(label="Invert", key="invert_steps_permutation", value=False)
    with toggle_cols[1]:
        st.toggle(
            label="Autotagger",
            key="autotagger_enabled",
            value=False,
        )
    with toggle_cols[2]:
        st.toggle(
            label="Solver",
            key="solver_enabled",
            value=False,
        )

    fig_steps_permutation = invert(steps_permutation) if invert_steps else steps_permutation
    fig_steps = plot_cube_state(permutation=fig_steps_permutation)
    st.pyplot(fig_steps, width="content")

    return all_cookies


def solver(session: SessionStateProxy, cookie_manager: stx.CookieManager) -> None:
    """Render the solver.

    Args:
        session (SessionStateProxy): Session state proxy.
        cookie_manager (stx.CookieManager): Cookie manager.
    """
    # Get cookies from app function to avoid duplicate get_all() calls
    all_cookies = app(session, cookie_manager, tool="Solver")

    if st.session_state.get("autotagger_enabled", True):
        move_meta = MoveMeta.from_cube_size(CUBE_SIZE)
        attempt = Attempt(
            scramble=session["scramble"],
            steps=session["steps"],
            move_meta=move_meta,
            metric=DEFAULT_METRIC,
            cleanup_final=True,
        )
        st.code(attempt.compile(width=80), language=None)

    if st.session_state.get("solver_enabled", False):
        # Initialize solutions in session state if not present
        if "solver_solutions" not in session:
            cached_solutions_str = all_cookies.get("solver_solutions", "")
            if cached_solutions_str:
                try:
                    cached_solutions = json.loads(cached_solutions_str)
                    if isinstance(cached_solutions, list) and all(
                        isinstance(item, dict) for item in cached_solutions
                    ):
                        session["solver_solutions"] = cached_solutions
                    else:
                        session["solver_solutions"] = []
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
                search_summary = solve_pattern(
                    sequence=sum((session["scramble"], *session["steps"]), start=MoveSequence()),
                    generator=MoveGenerator.from_str(generator),
                    algorithms=None,
                    goal=Goal(goal),
                    subset=subset,
                    max_search_depth=max_search_depth,
                    n_solutions=n_solutions,
                    search_inverse=(search_strategy == "Inverse"),
                )
            if search_summary.status is Status.Success:
                if len(search_summary.solutions) == 0:
                    st.warning(f"Goal '{goal}' is already solved!")
                else:
                    steps_sequence = sum(session["steps"], start=MoveSequence())
                    move_meta = MoveMeta.from_cube_size(CUBE_SIZE)
                    cleaned_steps = cleanup(steps_sequence, move_meta)
                    scramble_state = get_rubiks_cube_state(
                        sequence=session["scramble"],
                        orientate_after=True,
                    )
                    initial_state = get_rubiks_cube_state(
                        sequence=steps_sequence,
                        initial_permutation=scramble_state,
                        orientate_after=True,
                    )

                    # Store solution metadata
                    solutions_metadata: list[dict[str, int | str | None]] = []
                    for solution in search_summary.solutions:
                        solution_moves = measure(solution, metric=DEFAULT_METRIC)
                        combined_sequence = cleanup(cleaned_steps + solution, move_meta)
                        total_moves = measure(combined_sequence, metric=DEFAULT_METRIC)
                        cancellations = (
                            measure(cleaned_steps, metric=DEFAULT_METRIC)
                            + solution_moves
                            - measure(combined_sequence, metric=DEFAULT_METRIC)
                        )
                        final_state = get_rubiks_cube_state(
                            sequence=solution,
                            initial_permutation=initial_state,
                            orientate_after=True,
                        )
                        tag, subset_tag = autotag_permutation_with_subset(final_state)
                        solutions_metadata.append(
                            {
                                "solution": str(solution),
                                "tag": tag,
                                "subset": subset_tag,
                                "moves": solution_moves,
                                "total": total_moves,
                                "cancellations": cancellations,
                            }
                        )

                    # Combine with cached solutions (avoid duplicates)
                    all_solutions = cached_solutions.copy()
                    existing = {
                        item.get("solution") for item in all_solutions if isinstance(item, dict)
                    }
                    for solution in solutions_metadata:
                        if solution["solution"] not in existing:
                            all_solutions.append(solution)
                            existing.add(solution["solution"])

                    # Update session state first (this is the source of truth)
                    session["solver_solutions"] = all_solutions
                    cached_solutions = all_solutions

                    # Save to cookies for persistence
                    try:
                        solutions_str = json.dumps(all_solutions)
                        cookie_manager.set(
                            cookie="solver_solutions",
                            val=solutions_str,
                            key="solver_solutions_save",
                        )
                    except Exception:
                        pass  # Silently continue if cookie setting fails

            elif search_summary.status is Status.Failure:
                st.warning("Solver found no solutions!")

        # Display all solutions
        if cached_solutions:
            st.subheader(f"Solutions ({len(cached_solutions)} total)")

            for idx, solution in enumerate(cached_solutions):
                if not isinstance(solution, dict):
                    continue
                solution_label = str(solution.get("solution", ""))
                tag = str(solution.get("tag", ""))
                subset_tag = solution.get("subset")
                moves = solution.get("moves")
                total = solution.get("total")
                cancellations = solution.get("cancellations")
                if tag:
                    solution_label += f"  // {tag}"
                    if isinstance(subset_tag, str) and subset_tag:
                        solution_label += f" [{subset_tag}]"
                if isinstance(moves, int):
                    if isinstance(total, int):
                        if isinstance(cancellations, int) and cancellations > 0:
                            solution_label += f" ({moves}-{cancellations}/{total})"
                        else:
                            solution_label += f" ({moves}/{total})"
                    else:
                        solution_label += f" ({moves}"
                        if isinstance(cancellations, int) and cancellations > 0:
                            solution_label += f"-{cancellations}"
                        solution_label += ")"
                if st.button(
                    solution_label,
                    key=f"solver_solution_{idx}",
                    help="Add to steps",
                    width="stretch",
                ):
                    current_steps_value = st.session_state.get(
                        "steps_input", all_cookies.get("steps_input", "")
                    )
                    updated_steps = current_steps_value.rstrip()
                    if updated_steps:
                        updated_steps += "\n"
                    updated_steps += str(solution.get("solution", ""))
                    st.session_state["steps_input_pending"] = updated_steps
                    with contextlib.suppress(Exception):
                        cookie_manager.set(
                            cookie="steps_input", val=updated_steps, key="steps_input_click"
                        )
                    st.rerun()


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
  "eo": {
    "goals": ["eo-fb", "eo-lr", "eo-ud"],
    "max_length": 7,
    "n_solutions": 1,
    "search_solutions": 20,
    "generator": "<L, R, F, B, U, D>"
  },
  "dr": {
    "goals": ["dr-ud", "dr-fb", "dr-lr"],
    "max_length": 10,
    "n_solutions": 1,
    "search_solutions": 10,
    "generator": "<L, R, F, B, U, D>",
    "transition": {
      "allowed_prev_goals": {
        "dr-ud": ["eo-fb", "eo-lr"],
        "dr-fb": ["eo-lr", "eo-ud"],
        "dr-lr": ["eo-fb", "eo-ud"]
      },
      "generator_by_prev_goal": {
        "eo-fb": "<L, R, F2, B2, U, D>",
        "eo-lr": "<L2, R2, F, B, U, D>",
        "eo-ud": "<L, R, F, B, U2, D2>"
      }
    }
  },
  "htr": {
    "goals": ["htr-like"],
    "max_length": 12,
    "n_solutions": 1,
    "search_solutions": 50,
    "subset_filters": ["real"],
    "generator": "<L2, R2, F2, B2, U, D>",
    "transition": {
      "generator_by_prev_goal": {
        "dr-ud": "<L2, R2, F2, B2, U, D>",
        "dr-lr": "<L, R, F2, B2, U2, D2>",
        "dr-fb": "<L2, R2, F, B, U2, D2>"
      }
    }
  },
  "finish": {
    "goals": ["solved"],
    "max_length": 10,
    "n_solutions": 1,
    "generator": "<L2, R2, F2, B2, U2, D2>"
  }
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
