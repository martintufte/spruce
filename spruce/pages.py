from __future__ import annotations

import contextlib
import json
import logging
import math
from functools import lru_cache
from functools import partial
from typing import TYPE_CHECKING
from typing import Any
from typing import Final

import streamlit as st

from spruce.autotagger import PatternTagger
from spruce.autotagger import autotag_permutation
from spruce.autotagger.attempt import Attempt
from spruce.beam_search.plan import BEAM_PLANS
from spruce.beam_search.plan import PlanName
from spruce.beam_search.solver import beam_search
from spruce.beam_search.solver import build_step_contexts
from spruce.configuration.paths import OUTPUT_DIR
from spruce.graphics import plot_puzzle
from spruce.move.meta import MoveMeta
from spruce.move.sequence import MoveSequence
from spruce.move.sequence import cleanup
from spruce.move.sequence import measure
from spruce.move.sequence import sequence_from_word
from spruce.move.sequence import unniss
from spruce.parsing import format_generator
from spruce.parsing import parse_generator
from spruce.parsing import parse_scramble
from spruce.parsing import parse_steps
from spruce.puzzle.cube.goals import Goal
from spruce.puzzle.cube.variants import Variant
from spruce.representation import get_permutation
from spruce.representation.utils import invert
from spruce.serialization.converter import create_converter
from spruce.serialization.resources import ResourceHandler
from spruce.solver import solve_patterns
from spruce.solver.enumeration import SearchSide
from spruce.solver.enumeration import Status

if TYPE_CHECKING:
    import extra_streamlit_components as stx
    from streamlit.runtime.state import SessionStateProxy

    from spruce.configuration import AppConfig
    from spruce.puzzle.cube.metrics import Metric


LOGGER: Final = logging.getLogger(__name__)


@lru_cache
def _solver_handler(plan_name: str) -> ResourceHandler:
    """Return a ResourceHandler rooted at the fixed per-plan solver directory."""
    return ResourceHandler(
        resource_dir=OUTPUT_DIR / "solvers" / plan_name,
        converter=create_converter(),
    )


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
        session_state["scramble"] = parse_scramble(raw_scramble, move_meta=move_meta)
        with contextlib.suppress(Exception):
            cookie_manager.set(cookie="raw_scramble", val=raw_scramble, key="raw_scramble")
    permutation = get_permutation(
        sequence=session_state["scramble"],
        move_meta=move_meta,
    )

    # Plot the scramble permutation
    invert_scramble = st.toggle(label="Invert", key="invert_scramble_permutation")
    fig_permutation = invert(permutation) if invert_scramble else permutation
    fig_scramble = plot_puzzle(fig_permutation, puzzle=move_meta.puzzle)
    st.pyplot(fig_scramble, width="content")

    # Input steps
    if "raw_steps" not in session_state:
        session_state["raw_steps"] = all_cookies.get("raw_steps", "")
    if "raw_steps_pending" in session_state:
        session_state["raw_steps"] = session_state.pop("raw_steps_pending")
    raw_steps = st.text_area(
        label="Steps",
        placeholder="Step  // Comment\n...",
        height=200,
        key="raw_steps",
    )
    if raw_steps is not None:
        session_state["steps"] = parse_steps(raw_steps, move_meta=move_meta)
        with contextlib.suppress(Exception):
            cookie_manager.set(cookie="raw_steps", val=raw_steps, key="raw_steps")

    # Plot the steps permutation
    steps_permutation = get_permutation(
        sequence=sum(session_state["steps"], start=MoveSequence()),
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
    fig_steps = plot_puzzle(permutation=fig_steps_permutation, puzzle=move_meta.puzzle)
    st.pyplot(fig_steps, width="content")

    return all_cookies


def store_solutions(
    cached_solutions: list[dict[str, Any]],
    session_state: SessionStateProxy,
    cookie_manager: stx.CookieManager,
    solutions: list[MoveSequence],
    move_meta: MoveMeta,
    metric: Metric,
    display_text_by_solution: dict[str, str],
) -> int:
    """Store the solutions in the session state and cookies."""

    steps_sequence = sum(session_state["steps"], start=MoveSequence())
    cleaned_steps = cleanup(steps_sequence, move_meta)
    cleaned_steps_moves = measure(cleaned_steps, metric=metric)
    scramble_permutation = get_permutation(
        sequence=session_state["scramble"],
        move_meta=move_meta,
        orientate_after=True,
    )
    initial_permutation = get_permutation(
        sequence=steps_sequence,
        move_meta=move_meta,
        initial_permutation=scramble_permutation,
        orientate_after=True,
    )

    solutions_metadata: list[dict[str, int | str | None]] = []
    for solution in solutions:
        solution_moves = measure(solution, metric=metric)
        final_sequence = cleaned_steps + solution
        final_permutation = get_permutation(
            sequence=solution,
            move_meta=move_meta,
            initial_permutation=initial_permutation,
            orientate_after=True,
        )
        tag = autotag_permutation(
            final_permutation,
            move_meta=move_meta,
            include_subset=True,
        )

        # Include normal <-> inverse cancellations when the result is solved.
        if tag == "solved":
            final_sequence = unniss(final_sequence, move_meta=move_meta)

        cleaned_final_sequence = cleanup(final_sequence, move_meta)
        total_moves = measure(cleaned_final_sequence, metric=metric)
        cancellations = cleaned_steps_moves + solution_moves - total_moves

        solution_key = str(solution)
        steps_display = display_text_by_solution.get(solution_key)
        solutions_metadata.append(
            {
                "solution": solution_key,
                "steps_to_add": steps_display if steps_display is not None else solution_key,
                "steps_display": steps_display,
                "tag": tag,
                "moves": solution_moves,
                "total": total_moves,
                "cancellations": cancellations,
            },
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

    def _solution_sort_key(item: dict[str, int | str | None]) -> tuple[float, float, str]:
        total = item.get("total")
        moves = item.get("moves")
        return (
            total if isinstance(total, int) else math.inf,
            moves if isinstance(moves, int) else math.inf,
            str(item.get("solution", "")),
        )

    all_solutions.sort(
        key=lambda item: (
            _solution_sort_key(item) if isinstance(item, dict) else (math.inf, math.inf, str(item))
        ),
    )

    session_state["solver_solutions"] = all_solutions
    # Update in place so the caller's list reflects the merge within the same rerun
    cached_solutions[:] = all_solutions

    with contextlib.suppress(Exception):
        solutions_str = json.dumps(all_solutions)
        cookie_manager.set(
            cookie="solver_solutions",
            val=solutions_str,
            key="solver_solutions_save",
        )
    return len(solutions_metadata)


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
    puzzle = app_cfg.puzzle
    metric = app_cfg.metric

    # Setup the MoveMeta and the AutoTagger
    move_meta = MoveMeta.from_puzzle(puzzle)
    autotagger = PatternTagger.from_move_meta(move_meta=move_meta)

    # Render the user input boxes and visualizations
    all_cookies = app_input(session_state, cookie_manager, move_meta=move_meta)

    # Render the autotagger
    if session_state["autotagger_enabled"]:
        attempt = Attempt.from_scramble_and_steps(
            scramble=session_state["scramble"],
            steps=session_state["steps"],
            move_meta=move_meta,
            metric=metric,
            cleanup_final=True,
        )
        st.code(attempt.compile(autotagger, width=80), language=None)

    # Render the solver
    if session_state["solver_enabled"]:
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

        st.subheader("Settings")
        first_row = st.columns([2, 2, 1])
        with first_row[0]:
            goal_str = st.selectbox(
                label="Goal",
                options=goal_options,
                key="pattern",
            )
            goal = Goal(goal_str)
        with first_row[1]:
            solve_strategy = st.selectbox(
                label="Strategy",
                options=list(SearchSide),
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

        variants = [variant.value for variant in autotagger.patterns[goal].variants]

        second_row = st.columns([2, 2, 1])
        with second_row[0]:
            variant_list = st.multiselect(
                label="Variants",
                options=variants,
                key="variants",
            )
        with second_row[1]:
            generator = st.text_input(
                label="Generator",
                value=format_generator(move_meta.default_generator, move_meta=move_meta),
                key="generator",
            )
        with second_row[2]:
            max_solutions = st.number_input(
                label="Max solutions",
                value=10,
                min_value=1,
                max_value=500,
                key="max_solutions",
            )

        third_row = st.columns([2, 2, 1])
        with third_row[0]:
            beam_plan_name = st.selectbox(
                label="Beam Plan",
                options=[p.value for p in PlanName],
                key="beam_plan",
            )
        with third_row[1]:
            beam_width = st.number_input(
                label="Beam Width",
                value=5,
                min_value=1,
                max_value=500,
                key="beam_width",
            )
        with third_row[2]:
            beam_max_solutions = st.number_input(
                label="Max solutions",
                value=10,
                min_value=1,
                max_value=20,
                key="max_solutions_beam",
            )

        # Add solve controls
        col_solve, col_beam_build, col_beam_solve, col_clear = st.columns([2, 2, 2, 1])

        with col_solve:
            solve_clicked = st.button("Solve", type="primary", width="stretch")
        with col_beam_build:
            beam_build_clicked = st.button("Build", type="secondary", width="stretch")
        with col_beam_solve:
            contexts_built = _solver_handler(beam_plan_name).step_contexts_path.exists()
            beam_solve_clicked = st.button(
                "Solve (beam)",
                type="primary",
                width="stretch",
                disabled=not contexts_built,
            )
        with col_clear:
            clear_clicked = st.button("Clear", type="secondary", width="stretch")

        if contexts_built:
            st.caption(f"Solver built for plan: **{beam_plan_name}**")
        else:
            st.caption("No solver built yet — click **Build** first.")

        # Handle clear button
        if clear_clicked:
            session_state["solver_solutions"] = []
            cached_solutions = []
            try:
                cookie_manager.set(cookie="solver_solutions", val="", key="solver_solutions_clear")
            except Exception:
                st.warning("Could not clear solutions from cookies, but cleared from session")

        sequence_to_solve = sum(
            (session_state["scramble"], *session_state["steps"]),
            start=MoveSequence(),
        )

        solutions_to_store: list[MoveSequence] = []
        display_text_by_solution: dict[str, str] = {}

        # Handle solver button
        if solve_clicked:
            selected_generator = parse_generator(generator, move_meta=move_meta)
            selected_variants = [Variant(variant) for variant in variant_list]

            # The solver works on plain labelled patterns, so resolve the goal here
            pattern = patterns[goal]
            target_patterns = {
                variant.value: pattern[variant]
                for variant in (selected_variants or list(pattern.variants))
            }

            with st.spinner("Searching for solutions.."):
                search_summary = solve_patterns(
                    get_permutation(sequence=sequence_to_solve, move_meta=move_meta),
                    actions=move_meta.get_actions(generator=selected_generator),
                    patterns=target_patterns,
                    validator=pattern.validator,
                    validator_key=goal.value if pattern.validator is not None else None,
                    max_search_depth=max_search_depth,
                    max_solutions=max_solutions,
                    search_side=solve_strategy,
                )

            if search_summary.solutions:
                solutions_to_store = sorted(
                    (
                        sequence_from_word(
                            solution.word,
                            on_inverse=solution.side is SearchSide.inverse,
                        )
                        for solution in search_summary.solutions
                    ),
                    key=partial(measure, metric=metric),
                )
            elif search_summary.status is Status.success:
                st.warning(f"Goal '{goal}' is already solved!")
            else:
                st.warning("Solver found no solutions!")

        # Handle beam build button
        if beam_build_clicked:
            selected_plan = BEAM_PLANS[PlanName(beam_plan_name)]
            with st.spinner(f"Building solver for plan '{beam_plan_name}'…"):
                contexts = build_step_contexts(plan=selected_plan, move_meta=move_meta)
                handler = _solver_handler(beam_plan_name)
                handler.save_step_contexts(contexts)
                handler.save_plan_name(beam_plan_name)
            st.success(f"Solver built for plan: **{beam_plan_name}**")
            st.rerun()

        # Handle beam solve button
        if beam_solve_clicked:
            selected_plan = BEAM_PLANS[PlanName(beam_plan_name)]
            contexts = _solver_handler(beam_plan_name).load_step_contexts()
            with st.spinner("Searching for beam solutions…"):
                beam_summary = beam_search(
                    sequence=sequence_to_solve,
                    plan=selected_plan,
                    beam_width=beam_width,
                    metric=metric,
                    max_solutions=beam_max_solutions,
                    contexts=contexts,
                )
            if beam_summary.status is Status.success and beam_summary.solutions:
                for beam_solution in beam_summary.solutions:
                    solution = beam_solution.sequence
                    solutions_to_store.append(solution)
                    display_text_by_solution[str(solution)] = "\n".join(
                        str(step) for step in beam_solution.steps
                    )
            else:
                st.warning("Beam search found no solutions!")

        # Store solutions from either solver
        if solutions_to_store:
            store_solutions(
                cached_solutions=cached_solutions,
                session_state=session_state,
                cookie_manager=cookie_manager,
                solutions=solutions_to_store,
                move_meta=move_meta,
                metric=metric,
                display_text_by_solution=display_text_by_solution,
            )

        # Display all solutions
        if cached_solutions:
            st.subheader(f"Solutions ({len(cached_solutions)} total)")

            for idx, solution in enumerate(cached_solutions):
                assert isinstance(solution, dict)

                solution_label = str(solution.get("solution", ""))
                tag = str(solution.get("tag", ""))
                moves = solution.get("moves")
                total = solution.get("total")
                cancellations = solution.get("cancellations")
                steps_display = solution.get("steps_display")
                assert isinstance(moves, int)
                assert isinstance(total, int)
                assert isinstance(cancellations, int)

                # If solution has multiple lines, replace with pipe " | "
                if isinstance(steps_display, str):
                    solution_label = steps_display.replace("\n", " | ")

                # Add comment
                solution_label += f"  // {tag} ({moves}"
                if cancellations > 0:
                    solution_label += f"-{cancellations}"
                solution_label += f"/{total})"

                # Clicking the solution trigger adding it to steps
                if st.button(
                    solution_label,
                    key=f"solver_solution_{idx}",
                    help="Add to steps",
                    width="stretch",
                ):
                    current_steps_value = session_state.get(
                        "raw_steps",
                        all_cookies.get("raw_steps", ""),
                    )
                    updated_steps = current_steps_value.rstrip()
                    steps_to_add = solution.get("steps_to_add") or solution.get("solution") or ""
                    # An empty MoveSequence stringifies to "None"; nothing to add then.
                    if steps_to_add and steps_to_add != "None":
                        if updated_steps:
                            updated_steps += "\n"
                        updated_steps += str(steps_to_add)

                    # Add pending raw steps and update cookie manager
                    session_state["raw_steps_pending"] = updated_steps
                    with contextlib.suppress(Exception):
                        cookie_manager.set(
                            cookie="raw_steps",
                            val=updated_steps,
                            key="raw_steps_click",
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
