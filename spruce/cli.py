from __future__ import annotations

from typing import Final

import click

from spruce.move.meta import MoveMeta
from spruce.move.sequence import MoveSequence
from spruce.move.sequence import cleanup
from spruce.move.sequence import invert as invert_sequence

DEFAULT_CUBE_SIZE: Final = 3


def _parse_sequence(sequence: tuple[str, ...]) -> MoveSequence:
    if not sequence:
        raise click.UsageError("Missing move sequence.")

    try:
        return MoveSequence.from_str(" ".join(sequence))
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc


@click.command()
@click.argument("sequence", nargs=-1)
def up(sequence: tuple[str, ...]) -> None:
    """Cleanup a move sequence."""
    move_sequence = _parse_sequence(sequence)
    move_meta = MoveMeta.from_cube_size(cube_size=DEFAULT_CUBE_SIZE)
    cleaned_sequence = cleanup(move_sequence, move_meta)
    click.echo(str(cleaned_sequence))


@click.command()
@click.argument("sequence", nargs=-1)
def invert(sequence: tuple[str, ...]) -> None:
    """Invert a move sequence."""
    move_sequence = _parse_sequence(sequence)
    move_meta = MoveMeta.from_cube_size(cube_size=DEFAULT_CUBE_SIZE)
    inverted_sequence = invert_sequence(move_sequence, move_meta)
    click.echo(str(inverted_sequence))
