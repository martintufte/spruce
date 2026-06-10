from __future__ import annotations

import click

from spruce.cli import invert
from spruce.cli import up


@click.group()
def main() -> None:
    """Rubik's cube move-sequence tools."""


main.add_command(up)
main.add_command(invert)


if __name__ == "__main__":
    main()
