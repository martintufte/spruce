"""CLI entry points for training and running the beam solver."""

from __future__ import annotations

import json
import logging
from pathlib import Path  # noqa: TC003
from typing import Annotated
from typing import Final

import typer

from rubiks_cube.beam_search.plan import BEAM_PLANS
from rubiks_cube.beam_search.plan import PlanName
from rubiks_cube.beam_search.solver import beam_search
from rubiks_cube.beam_search.solver import build_step_contexts
from rubiks_cube.configuration import LogLevel  # noqa: TC001
from rubiks_cube.configuration.enumeration import Metric
from rubiks_cube.configuration.logging import configure_logging
from rubiks_cube.move.meta import MoveMeta
from rubiks_cube.move.sequence import measure
from rubiks_cube.parsing import parse_scramble
from rubiks_cube.serialization.converter import create_converter
from rubiks_cube.serialization.resources import ResourceHandler

LOGGER: Final = logging.getLogger(__name__)

app = typer.Typer(
    name="spruce",
    help="Rubik's cube beam solver.",
    no_args_is_help=True,
)

_PLAN_NAMES = [p.value for p in PlanName]
_METRIC_NAMES = [m.name for m in Metric]

_PLAN_NAME_FILE = "plan_name.json"


def _save_plan_name(resource_dir: Path, plan_name: str) -> None:
    (resource_dir / _PLAN_NAME_FILE).write_text(json.dumps({"plan_name": plan_name}))


def _load_plan_name(resource_dir: Path) -> str:
    path = resource_dir / _PLAN_NAME_FILE
    if not path.exists():
        typer.echo(
            f"No plan metadata found at {path}. Was 'train' run in this directory?",
            err=True,
        )
        raise typer.Exit(code=1)
    return json.loads(path.read_text())["plan_name"]


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

    beam_plan = BEAM_PLANS[plan_key]
    move_meta = MoveMeta.from_cube_size(cube_size=beam_plan.cube_size)
    resource_handler = ResourceHandler(resource_dir=resource_dir, converter=create_converter())

    LOGGER.info(f"Building solver for plan '{plan}' (cube size {beam_plan.cube_size})…")
    contexts = build_step_contexts(plan=beam_plan, move_meta=move_meta)

    resource_handler.save_step_contexts(contexts)
    _save_plan_name(resource_dir, plan)
    LOGGER.info(f"Solver saved to {resource_handler.step_contexts_path}")
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
            f"No solver found at {resource_handler.step_contexts_path}. " "Run 'train' first.",
            err=True,
        )
        raise typer.Exit(code=1)

    plan_name = _load_plan_name(resource_dir)
    beam_plan = BEAM_PLANS[PlanName(plan_name)]

    LOGGER.info(
        f"Loading solver for plan '{plan_name}' from {resource_handler.step_contexts_path}.."
    )
    contexts = resource_handler.load_step_contexts()

    sequence = parse_scramble(scramble)
    LOGGER.info(f"Solving scramble: {sequence}")
    summary = beam_search(
        sequence=sequence,
        plan=beam_plan,
        beam_width=beam_width,
        max_solutions=max_solutions,
        max_time=max_time,
        metric=metric,
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
