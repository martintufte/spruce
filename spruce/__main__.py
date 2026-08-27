"""CLI entry points for training and running the beam solver."""

from __future__ import annotations

import logging
from functools import partial
from pathlib import Path  # noqa: TC003
from typing import Annotated
from typing import Final

import typer

from spruce.autotagger.pattern import get_catalogue
from spruce.configuration import LogLevel  # noqa: TC001
from spruce.configuration.logging import configure_logging
from spruce.parsing import parse_scramble
from spruce.puzzle.cube.group import build_move_meta
from spruce.puzzle.cube.metrics import Metric
from spruce.puzzle.cube.metrics import measure
from spruce.puzzle.cube.plans import BEAM_PLANS
from spruce.puzzle.cube.plans import PlanName
from spruce.search.beam import beam_search
from spruce.search.beam import build_step_contexts
from spruce.serialization.converter import create_converter
from spruce.serialization.resources import ResourceHandler

LOGGER: Final = logging.getLogger(__name__)

app = typer.Typer(
    name="spruce",
    help="Rubik's cube beam solver.",
    no_args_is_help=True,
)

_PLAN_NAMES = [p.value for p in PlanName]
_METRIC_NAMES = [m.name for m in Metric]


@app.command()
def train(
    plan: Annotated[
        str,
        typer.Argument(help=f"Beam plan to build. Choices: {_PLAN_NAMES}"),
    ],
    resource_dir: Annotated[
        Path,
        typer.Option("--resource-dir", "-d", help="Directory where solver files are saved."),
    ],
    log_level: Annotated[
        LogLevel,
        typer.Option("--log-level", "-l", help="Logging level."),
    ] = "info",
) -> None:
    """Build a beam solver for PLAN and save it to RESOURCE_DIR.

    Run this once per plan. The saved solver can then be reused across many
    scrambles with the 'infer' command without paying the build cost again.
    """
    configure_logging(level=log_level)

    try:
        plan_key = PlanName(plan)
    except ValueError:
        typer.echo(f"Unknown plan '{plan}'. Choices: {_PLAN_NAMES}", err=True)
        raise typer.Exit(code=1) from None

    cube_plan = BEAM_PLANS[plan_key]
    move_meta = build_move_meta(puzzle=cube_plan.puzzle)
    resource_handler = ResourceHandler(resource_dir=resource_dir, converter=create_converter())

    LOGGER.info("Building solver for plan '%s' (puzzle %s)…", plan, cube_plan.puzzle)
    contexts = build_step_contexts(
        plan=cube_plan.plan,
        move_meta=move_meta,
        patterns=get_catalogue(puzzle=cube_plan.puzzle),
    )

    resource_handler.save_step_contexts(contexts)
    resource_handler.save_plan_name(plan)
    LOGGER.info("Solver saved to %s", resource_handler.step_contexts_path)
    typer.echo(f"Solver built and saved to: {resource_handler.step_contexts_path}")


@app.command()
def infer(
    scramble: Annotated[
        str,
        typer.Argument(help="Scramble sequence to solve, e.g. \"R' U' F ...\"."),
    ],
    resource_dir: Annotated[
        Path,
        typer.Option("--resource-dir", "-d", help="Directory with the pre-built solver files."),
    ],
    log_level: Annotated[
        LogLevel,
        typer.Option("--log-level", "-l", help="Logging level."),
    ] = "info",
    beam_width: Annotated[
        int,
        typer.Option("--beam-width", "-w", min=1, help="Number of candidates kept between steps."),
    ] = 5,
    max_solutions: Annotated[
        int,
        typer.Option("--max-solutions", min=1, help="Maximum number of solutions to return."),
    ] = 1,
    max_time: Annotated[
        float,
        typer.Option("--max-time", min=0.0, help="Wall-clock time limit in seconds."),
    ] = 60.0,
    metric_name: Annotated[
        str,
        typer.Option(
            "--metric",
            help=f"Move-count metric used to rank solutions. Choices: {_METRIC_NAMES}",
        ),
    ] = "HTM",
) -> None:
    """Solve SCRAMBLE using the pre-built solver in RESOURCE_DIR.

    Run 'train' first to build the solver, then call this command for each
    scramble you want to solve. The expensive build step is skipped entirely.
    """
    configure_logging(level=log_level)

    if metric_name not in _METRIC_NAMES:
        typer.echo(f"Unknown metric '{metric_name}'. Choices: {_METRIC_NAMES}", err=True)
        raise typer.Exit(code=1)
    metric = Metric[metric_name]

    resource_handler = ResourceHandler(resource_dir=resource_dir, converter=create_converter())

    if not resource_handler.step_contexts_path.exists():
        typer.echo(
            f"No solver found at {resource_handler.step_contexts_path}. Run 'train' first.",
            err=True,
        )
        raise typer.Exit(code=1)

    if not resource_handler.plan_name_path.exists():
        typer.echo(
            f"No plan metadata found at {resource_handler.plan_name_path}. "
            "Was 'train' run in this directory?",
            err=True,
        )
        raise typer.Exit(code=1)
    plan_name = resource_handler.load_plan_name()
    cube_plan = BEAM_PLANS[PlanName(plan_name)]

    LOGGER.info(
        "Loading solver for plan '%s' from %s..",
        plan_name,
        resource_handler.step_contexts_path,
    )
    contexts = resource_handler.load_step_contexts()

    move_meta = build_move_meta(puzzle=cube_plan.puzzle)
    sequence = parse_scramble(scramble, move_meta=move_meta)
    LOGGER.info("Solving scramble: %s", sequence)
    summary = beam_search(
        sequence=sequence,
        plan=cube_plan.plan,
        move_meta=move_meta,
        beam_width=beam_width,
        cost=partial(measure, metric=metric),
        max_solutions=max_solutions,
        max_time=max_time,
        contexts=contexts,
    )

    if not summary.solutions:
        typer.echo("No solutions found.", err=True)
        raise typer.Exit(code=1)

    typer.echo(f"Found {len(summary.solutions)} solution(s) in {summary.walltime:.2f}s:\n")
    for i, sol in enumerate(summary.solutions, start=1):
        moves = measure(sol.sequence, metric=metric)
        typer.echo(f"[{i}] {moves} {metric.value}  —  {sol.sequence}")
        for j, step in enumerate(sol.steps, start=1):
            typer.echo(f"    Step {j}: {step}")
        typer.echo()


if __name__ == "__main__":
    app()
