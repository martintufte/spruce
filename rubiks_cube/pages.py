from __future__ import annotations

import contextlib
import json
import logging
from functools import partial
from typing import TYPE_CHECKING
from typing import Final

import streamlit as st
from annotated_text import parameters

from rubiks_cube.autotagger import PatternTagger
from rubiks_cube.autotagger import autotag_permutation
from rubiks_cube.autotagger.attempt import Attempt
from rubiks_cube.beam_search.plan import BEAM_PLANS
from rubiks_cube.beam_search.solver import beam_search as solve_beam_search
from rubiks_cube.configuration import DEFAULT_GENERATOR_MAP
from rubiks_cube.configuration import AppConfig
from rubiks_cube.configuration.enumeration import Goal
from rubiks_cube.configuration.enumeration import SolveStrategy
from rubiks_cube.configuration.enumeration import Status
from rubiks_cube.graphics import plot_permutation
from rubiks_cube.move.generator import MoveGenerator
from rubiks_cube.move.meta import MoveMeta
from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.move.sequence import cleanup
from rubiks_cube.move.sequence import measure
from rubiks_cube.move.sequence import unniss
from rubiks_cube.parsing import parse_scramble
from rubiks_cube.parsing import parse_steps
from rubiks_cube.representation import get_rubiks_cube_permutation
from rubiks_cube.representation.utils import invert
from rubiks_cube.solver import solve_pattern

if TYPE_CHECKING:
    import extra_streamlit_components as stx
    from streamlit.runtime.state import SessionStateProxy

LOGGER: Final = logging.getLogger(__name__)

parameters.PADDING = "0.25rem 0.4rem"  # ty: ignore[invalid-assignment]
parameters.SHOW_LABEL_SEPARATOR = False  # ty: ignore[invalid-assignment]


def app_input(
    session_state: SessionStateProxy,
    cookie_manager: stx.CookieManager,
    move_meta: MoveMeta,
) -> dict[str, str]:
    """Render the input area of the app.

    Args:
        session (SessionStateProxy): Session state proxy.
        cookie_manager (stx.CookieManager): Cookie manager.
        move_meta (MoveMeta): Meta information about moves.

    Returns:
        dict[str, str]: All cookies loaded from the cookie manager.
    """
    st.subheader("Spruce")

    # Get all cookies to ensure they're loaded (only call this once)
    all_cookies = cookie_manager.get_all() or {}

    # Input raw scramble
    current_raw_scramble: str = all_cookies.get("raw_scramble", "")
    raw_scramble = st.text_input(
        label="Scramble",
        value=current_raw_scramble,
        placeholder="R' U' F ...",
        key="raw_scramble",
    )
    if raw_scramble is not None:
        session_state["scramble"] = parse_scramble(raw_scramble)
        with contextlib.suppress(Exception):
            cookie_manager.set(cookie="raw_scramble", val=raw_scramble, key="raw_scramble")
    permutation = get_rubiks_cube_permutation(
        sequence=session_state["scramble"],
        move_meta=move_meta,
    )

    # Plot the scramble permutation
    invert_scramble = st.toggle(label="Invert", key="invert_scramble_permutation")
    fig_permutation = invert(permutation) if invert_scramble else permutation
    fig_scramble = plot_permutation(fig_permutation, cube_size=move_meta.cube_size)
    st.pyplot(fig_scramble, width="content")

    # Input steps
    current_raw_steps = all_cookies.get("raw_steps", "")
    if "raw_steps_pending" in st.session_state:
        st.session_state["raw_steps"] = st.session_state.pop("raw_steps_pending")
    if "raw_steps" not in st.session_state:
        st.session_state["raw_steps"] = current_raw_steps
    raw_steps = st.text_area(
        label="Steps",
        value=st.session_state["raw_steps"],
        placeholder="Step  // Comment\n...",
        height=200,
        key="raw_steps",
    )
    if raw_steps is not None:
        session_state["steps"] = parse_steps(raw_steps)
        with contextlib.suppress(Exception):
            cookie_manager.set(cookie="raw_steps", val=raw_steps, key="raw_steps")

    # Plot the steps permutation
    steps_permutation = get_rubiks_cube_permutation(
        sequence=session_state["steps"].to_sequence(),
        move_meta=move_meta,
        initial_permutation=permutation,
    )
    toggle_cols = st.columns([1, 1, 1])
    with toggle_cols[0]:
        invert_steps = st.toggle(label="Invert", key="invert_steps_permutation")
    with toggle_cols[1]:
        st.toggle(label="Autotagger", key="autotagger_enabled")
    with toggle_cols[2]:
        st.toggle(label="Solver", key="solver_enabled")
    fig_steps_permutation = invert(steps_permutation) if invert_steps else steps_permutation
    fig_steps = plot_permutation(permutation=fig_steps_permutation, cube_size=move_meta.cube_size)
    st.pyplot(fig_steps, width="content")

    return all_cookies


def app(
    app_cfg: AppConfig,
    session_state: SessionStateProxy,
    cookie_manager: stx.CookieManager,
) -> None:
    """Render the app.

    Args:
        app_cfg (AppConfig): App configuration.
        session (SessionStateProxy): Session state proxy.
        cookie_manager (stx.CookieManager): Cookie manager.
    """
    # Configurations for the session
    cube_size = app_cfg.cube_size
    metric = app_cfg.metric

    # Setup the MoveMeta and the AutoTagger
    move_meta = MoveMeta.from_cube_size(cube_size)
    autotagger = PatternTagger.from_cube_size(cube_size)

    # Render the user input boxes and visualizations
    all_cookies = app_input(session_state, cookie_manager, move_meta=move_meta)

    # Render the autotagger
    if st.session_state["autotagger_enabled"]:
        attempt = Attempt.from_scramble_and_steps(
            scramble=session_state["scramble"],
            steps=session_state["steps"],
            move_meta=move_meta,
            metric=metric,
            cleanup_final=True,
        )
        st.code(attempt.compile(autotagger, width=80), language=None)

    # Render the solver
    if st.session_state["solver_enabled"]:
        # Initialize solutions in session state if not present
        if "solver_solutions" not in session_state:
            cached_solutions_str = all_cookies.get("solver_solutions", "")
            if cached_solutions_str:
                try:
                    cached_solutions = json.loads(cached_solutions_str)
                    if isinstance(cached_solutions, list) and all(
                        isinstance(item, dict) for item in cached_solutions
                    ):
                        session_state["solver_solutions"] = cached_solutions
                    else:
                        session_state["solver_solutions"] = []
                except Exception:
                    session_state["solver_solutions"] = []
            else:
                session_state["solver_solutions"] = []

        # Use session state as the source of truth
        cached_solutions = session_state["solver_solutions"]

        patterns = autotagger.patterns
        goal_options = [goal.value for goal in patterns]

        if Goal.htr.value not in goal_options:
            goal_options.append(Goal.htr.value)

        st.subheader("Settings")
        first_row = st.columns([2, 2, 1])
        with first_row[0]:
            goal = st.selectbox(
                label="Goal",
                options=goal_options,
                key="pattern",
            )
        solver_goal = Goal(goal)
        if solver_goal == Goal.htr:
            n_subsets = len(patterns[Goal.htr_like].patterns)
        else:
            n_subsets = len(patterns[solver_goal].patterns)

        with first_row[1]:
            solve_strategy = st.selectbox(
                label="Strategy",
                options=list(SolveStrategy),
                key="solve_strategy",
                format_func=lambda strategy: strategy.value.title(),
            )
        with first_row[2]:
            max_search_depth = st.number_input(
                label="Max depth",
                value=10,
                min_value=1,
                max_value=20,
                key="max_depth",
            )

        second_row = st.columns([2, 2, 1])
        with second_row[0]:
            generator = st.text_input(
                label="Generator",
                value=DEFAULT_GENERATOR_MAP[move_meta.cube_size],
                key="generator",
            )
        with second_row[1]:
            search_count_multiplier = 2 if solve_strategy is SolveStrategy.both else 1
            st.text_input(
                label="Number of searches",
                value=str(n_subsets * search_count_multiplier),
                disabled=True,
            )
        with second_row[2]:
            max_solutions = st.number_input(
                label="Max solutions",
                value=10,
                min_value=1,
                max_value=200,
                key="max_solutions",
            )

        third_row = st.columns([2, 2, 1])
        with third_row[0]:
            beam_plan_name = st.selectbox(
                label="Beam Plan",
                options=list(BEAM_PLANS),
                key="beam_plan",
            )
        with third_row[1]:
            beam_width = st.number_input(
                label="Beam Width",
                value=50,
                min_value=1,
                max_value=200,
                key="beam_width",
            )

        def _store_solutions(
            solutions: list[MoveSequence],
            move_meta: MoveMeta,
            steps_text_by_solution: dict[str, str] | None = None,
        ) -> int:
            nonlocal cached_solutions

            steps_sequence = sum(session_state["steps"], start=MoveSequence())
            cleaned_steps = cleanup(steps_sequence, move_meta)
            scramble_permutation = get_rubiks_cube_permutation(
                sequence=session_state["scramble"],
                move_meta=move_meta,
                orientate_after=True,
            )
            initial_permutation = get_rubiks_cube_permutation(
                sequence=steps_sequence,
                move_meta=move_meta,
                initial_permutation=scramble_permutation,
                orientate_after=True,
            )

            solutions_metadata: list[dict[str, int | str | None]] = []
            for solution in solutions:
                solution_moves = measure(solution, metric=metric)
                final_sequence = cleaned_steps + solution
                final_permutation = get_rubiks_cube_permutation(
                    sequence=solution,
                    move_meta=move_meta,
                    initial_permutation=initial_permutation,
                    orientate_after=True,
                )
                tag = autotag_permutation(
                    final_permutation, cube_size=move_meta.cube_size, include_subset=True
                )

                # Include normal <-> inverse cancellations when the result is solved.
                if tag == "solved":
                    final_sequence = unniss(final_sequence, move_meta=move_meta)

                cleaned_final_sequence = cleanup(final_sequence, move_meta)
                total_moves = measure(cleaned_final_sequence, metric=metric)
                cancellations = measure(cleaned_steps, metric=metric) + solution_moves - total_moves

                solutions_metadata.append(
                    {
                        "solution": str(solution),
                        "steps_to_add": (
                            steps_text_by_solution.get(str(solution), str(solution))
                            if steps_text_by_solution is not None
                            else str(solution)
                        ),
                        "steps_display": (
                            steps_text_by_solution.get(str(solution))
                            if steps_text_by_solution is not None
                            else None
                        ),
                        "tag": tag,
                        "moves": solution_moves,
                        "total": total_moves,
                        "cancellations": cancellations,
                    }
                )

            all_solutions = cached_solutions.copy()
            existing_idx: dict[str, int] = {
                str(item.get("solution")): idx
                for idx, item in enumerate(all_solutions)
                if isinstance(item, dict) and item.get("solution")
            }
            for solution in solutions_metadata:
                solution_key = str(solution["solution"])
                if solution_key not in existing_idx:
                    all_solutions.append(solution)
                    existing_idx[solution_key] = len(all_solutions) - 1
                else:
                    existing_entry = all_solutions[existing_idx[solution_key]]
                    if (
                        isinstance(existing_entry, dict)
                        and solution.get("steps_display")
                        and not existing_entry.get("steps_display")
                    ):
                        existing_entry["steps_display"] = solution["steps_display"]
                        existing_entry["steps_to_add"] = solution["steps_to_add"]

            def _solution_sort_key(item: dict[str, int | str | None]) -> tuple[int, int, str]:
                total = item.get("total")
                moves = item.get("moves")
                return (
                    total if isinstance(total, int) else 10**9,
                    moves if isinstance(moves, int) else 10**9,
                    str(item.get("solution", "")),
                )

            all_solutions.sort(
                key=lambda item: (
                    _solution_sort_key(item)
                    if isinstance(item, dict)
                    else (10**9, 10**9, str(item))
                )
            )

            session_state["solver_solutions"] = all_solutions
            cached_solutions = all_solutions

            with contextlib.suppress(Exception):
                solutions_str = json.dumps(all_solutions)
                cookie_manager.set(
                    cookie="solver_solutions",
                    val=solutions_str,
                    key="solver_solutions_save",
                )
            return len(solutions_metadata)

        # Add solve controls
        col_solve, col_beam_solve, col_clear = st.columns([2, 2, 1])

        with col_solve:
            solve_clicked = st.button("Solve", type="primary", width="stretch")
        with col_beam_solve:
            beam_solve_clicked = st.button("Beam Search", type="primary", width="stretch")
        with col_clear:
            clear_clicked = st.button("Clear", type="secondary", width="stretch")

        # Handle clear button
        if clear_clicked:
            session_state["solver_solutions"] = []
            cached_solutions = []
            try:
                cookie_manager.set(cookie="solver_solutions", val="", key="solver_solutions_clear")
            except Exception:
                st.warning("Could not clear solutions from cookies, but cleared from session")

        sequence_to_solve = sum(
            (session_state["scramble"], *session_state["steps"]), start=MoveSequence()
        )

        # Handle solver button
        if solve_clicked:
            selected_generator = MoveGenerator.from_str(generator)
            with st.spinner("Finding solutions.."):
                search_summary = solve_pattern(
                    sequence=sequence_to_solve,
                    move_meta=move_meta,
                    generator=selected_generator,
                    algorithms=None,
                    goal=solver_goal,
                    max_search_depth=max_search_depth,
                    max_solutions=max_solutions,
                    solve_strategy=solve_strategy,
                )

            if search_summary.solutions:
                stored_count = _store_solutions(
                    solutions=sorted(search_summary.solutions, key=partial(measure, metric=metric)),
                    move_meta=move_meta,
                )

                if stored_count == 0:
                    st.warning("Solver found no solutions!")

            elif search_summary.status is Status.Success:
                st.warning(f"Goal '{goal}' is already solved!")
            else:
                st.warning("Solver found no solutions!")

        # Handle beam solver button
        if beam_solve_clicked:
            selected_plan = BEAM_PLANS[beam_plan_name]
            with st.spinner("Finding beam solutions.."):
                beam_summary = solve_beam_search(
                    sequence=sequence_to_solve,
                    plan=selected_plan,
                    beam_width=int(beam_width),
                    max_solutions=max_solutions,
                )
            if beam_summary.status is Status.Success:
                if len(beam_summary.solutions) == 0:
                    st.warning("Beam solver found no solutions!")
                else:
                    beam_steps_text_by_solution: dict[str, str] = {}
                    for beam_solution in beam_summary.solutions:
                        non_empty_steps = [
                            str(step) for step in beam_solution.steps if len(step) > 0
                        ]
                        if non_empty_steps:
                            beam_steps_text_by_solution[str(beam_solution.sequence)] = "\n".join(
                                non_empty_steps
                            )
                    _store_solutions(
                        solutions=[solution.sequence for solution in beam_summary.solutions],
                        move_meta=move_meta,
                        steps_text_by_solution=beam_steps_text_by_solution,
                    )
            elif beam_summary.status is Status.Failure:
                st.warning("Beam solver found no solutions!")

        # Display all solutions
        if cached_solutions:
            st.subheader(f"Solutions ({len(cached_solutions)} total)")

            for idx, solution in enumerate(cached_solutions):
                if not isinstance(solution, dict):
                    continue
                solution_label = str(solution.get("solution", ""))
                tag = str(solution.get("tag", ""))
                moves = solution.get("moves")
                total = solution.get("total")
                cancellations = solution.get("cancellations")
                steps_display = solution.get("steps_display")
                if isinstance(steps_display, str) and steps_display:
                    solution_label = steps_display.replace("\n", " | ")
                if tag:
                    solution_label += f"  // {tag}"
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
                        "raw_steps", all_cookies.get("raw_steps", "")
                    )
                    updated_steps = current_steps_value.rstrip()
                    if updated_steps:
                        updated_steps += "\n"
                    updated_steps += str(solution.get("steps_to_add", solution.get("solution", "")))
                    st.session_state["raw_steps_pending"] = updated_steps
                    with contextlib.suppress(Exception):
                        cookie_manager.set(
                            cookie="raw_steps", val=updated_steps, key="raw_steps_click"
                        )
                    st.rerun()


def docs(session_state: SessionStateProxy, cookie_manager: stx.CookieManager) -> None:
    """Render the documentation.

    Args:
        session_state (SessionStateProxy): Session state proxy.
        cookie_manager (stx.CookieManager): Cookie manager.
    """
    st.header("Docs")
    st.markdown("Copyright © 2026 Martin Tufte")
