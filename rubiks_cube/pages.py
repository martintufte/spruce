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
from rubiks_cube.beam_search.solver import beam_search as solve_beam_search
from rubiks_cube.beam_search.template import EO_DR_HTR_PLAN
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
from rubiks_cube.move.sequence import unniss
from rubiks_cube.parsing import parse_scramble
from rubiks_cube.parsing import parse_steps
from rubiks_cube.representation import get_rubiks_cube_state
from rubiks_cube.representation.utils import invert
from rubiks_cube.solver import solve_pattern

if TYPE_CHECKING:
    import extra_streamlit_components as stx
    from streamlit.runtime.state import SessionStateProxy

    from rubiks_cube.beam_search.interface import BeamPlan

LOGGER: Final = logging.getLogger(__name__)
BEAM_PLANS: Final[dict[str, BeamPlan]] = {EO_DR_HTR_PLAN.name or "EO-DR-HTR": EO_DR_HTR_PLAN}
GENERATOR_BY_TAG: Final[dict[str, str]] = {
    "eo-fb": "<U, D, L, R, F2, B2>",
    "eo-lr": "<U, D, L2, R2, F, B>",
    "eo-ud": "<U2, D2, L, R, F, B>",
    "dr-ud": "<U, D, L2, R2, F2, B2>",
    "dr-lr": "<F2, B2, L, R, U2, D2>",
    "dr-fb": "<F, B, L2, R2, U2, D2>",
    "htr-like": "<U2, D2, L2, R2, F2, B2>",
}

parameters.PADDING = "0.25rem 0.4rem"  # ty: ignore[invalid-assignment]
parameters.SHOW_LABEL_SEPARATOR = False  # ty: ignore[invalid-assignment]


def _get_solution_display_tag_and_subset(
    tag: str,
    subset: str | None,
) -> tuple[str, str | None]:
    if tag == Goal.htr_like.value and subset == "real":
        return Goal.htr.value, None
    return tag, subset


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

    st.subheader("Spruce")

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

    # Display the autotagger compiled solution
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
        goal_options = [goal.value for goal in cubexes]

        if Goal.htr.value not in goal_options:
            goal_options.append(Goal.htr.value)

        # Update the generator from the pending generator
        if "generator_pending" in st.session_state:
            st.session_state["generator"] = st.session_state.pop("generator_pending")

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
            subset_names = cubexes[Goal.htr_like].names
        else:
            subset_names = cubexes[solver_goal].names

        with first_row[1]:
            search_strategy = st.selectbox(
                label="Strategy",
                options=["Normal", "Inverse", "Both"],
                key="search_strategy",
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
                value=DEFAULT_GENERATOR,
                key="generator",
            )
        with second_row[1]:
            search_count_multiplier = 2 if search_strategy == "Both" else 1
            st.text_input(
                label="Number of searches",
                value=str(len(subset_names) * search_count_multiplier),
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
            steps_text_by_solution: dict[str, str] | None = None,
        ) -> int:
            nonlocal cached_solutions

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

            solutions_metadata: list[dict[str, int | str | None]] = []
            for solution in solutions:
                solution_moves = measure(solution, metric=DEFAULT_METRIC)
                final_sequence = cleaned_steps + solution
                final_state = get_rubiks_cube_state(
                    sequence=solution,
                    initial_permutation=initial_state,
                    orientate_after=True,
                )
                tag, subset_tag = autotag_permutation_with_subset(final_state)

                # Include normal <-> inverse cancellations when the result is solved.
                if tag == "solved":
                    final_sequence = unniss(final_sequence)

                cleaned_final_sequence = cleanup(final_sequence, move_meta)
                total_moves = measure(cleaned_final_sequence, metric=DEFAULT_METRIC)
                cancellations = (
                    measure(cleaned_steps, metric=DEFAULT_METRIC) + solution_moves - total_moves
                )

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
                        "subset": subset_tag,
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

            session["solver_solutions"] = all_solutions
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
            session["solver_solutions"] = []
            cached_solutions = []
            try:
                cookie_manager.set(cookie="solver_solutions", val="", key="solver_solutions_clear")
            except Exception:
                st.warning("Could not clear solutions from cookies, but cleared from session")

        sequence_to_solve = sum((session["scramble"], *session["steps"]), start=MoveSequence())

        # Handle solver button
        if solve_clicked:
            selected_generator = MoveGenerator.from_str(generator)
            search_modes = (
                [False, True] if search_strategy == "Both" else [search_strategy == "Inverse"]
            )

            all_subset_solutions: list[MoveSequence] = []
            subset_statuses: list[Status] = []
            with st.spinner("Finding solutions.."):
                for subset in subset_names:
                    for search_inverse in search_modes:
                        search_summary = solve_pattern(
                            sequence=sequence_to_solve,
                            generator=selected_generator,
                            algorithms=None,
                            goal=solver_goal,
                            subset=subset,
                            max_search_depth=max_search_depth,
                            max_solutions=max_solutions,
                            search_inverse=search_inverse,
                        )
                        subset_statuses.append(search_summary.status)
                        all_subset_solutions.extend(search_summary.solutions)

            if all_subset_solutions:
                # Merge subset results and keep shortest unique sequences.
                unique_solutions = {str(solution): solution for solution in all_subset_solutions}
                max_results = max_solutions * len(search_modes)
                merged_solutions = sorted(unique_solutions.values(), key=measure)[:max_results]
                stored_count = _store_solutions(merged_solutions)

                if stored_count == 0:
                    st.warning("Solver found no solutions!")

            elif all(status is Status.Success for status in subset_statuses):
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
                        [solution.sequence for solution in beam_summary.solutions],
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
                subset_tag = solution.get("subset")
                moves = solution.get("moves")
                total = solution.get("total")
                cancellations = solution.get("cancellations")
                steps_display = solution.get("steps_display")
                if isinstance(steps_display, str) and steps_display:
                    solution_label = steps_display.replace("\n", " | ")
                if tag:
                    subset_text = subset_tag if isinstance(subset_tag, str) else None
                    tag, subset_text = _get_solution_display_tag_and_subset(tag, subset_text)
                    solution_label += f"  // {tag}"
                    if (
                        not (isinstance(steps_display, str) and steps_display)
                        and isinstance(subset_text, str)
                        and subset_text
                    ):
                        solution_label += f" [{subset_text}]"
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
                    tag_value = solution.get("tag")
                    if isinstance(tag_value, str) and tag_value in GENERATOR_BY_TAG:
                        st.session_state["generator_pending"] = GENERATOR_BY_TAG[tag_value]

                    current_steps_value = st.session_state.get(
                        "steps_input", all_cookies.get("steps_input", "")
                    )
                    updated_steps = current_steps_value.rstrip()
                    if updated_steps:
                        updated_steps += "\n"
                    updated_steps += str(solution.get("steps_to_add", solution.get("solution", "")))
                    st.session_state["steps_input_pending"] = updated_steps
                    with contextlib.suppress(Exception):
                        cookie_manager.set(
                            cookie="steps_input", val=updated_steps, key="steps_input_click"
                        )
                    st.rerun()


def docs(session: SessionStateProxy, cookie_manager: stx.CookieManager) -> None:
    """Render the documentation.

    Args:
        session (SessionStateProxy): Session state proxy.
        cookie_manager (stx.CookieManager): Cookie manager.
    """
    st.header("Docs")
    st.markdown("Copyright © 2025 Martin Tufte")
