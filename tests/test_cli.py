from __future__ import annotations

from click.testing import CliRunner

from spruce.cli import invert
from spruce.cli import up


def test_up_command() -> None:
    runner = CliRunner()

    result = runner.invoke(up, ["(R')", "L", "M'", "(S2)", "x2", "(z)"])

    assert result.exit_code == 0
    assert result.output.strip() == "L2 R' x' (R' F2 B2 z')"


def test_invert_command() -> None:
    runner = CliRunner()

    result = runner.invoke(invert, ["L", "M'", "x2", "(R'", "S2", "z)"])

    assert result.exit_code == 0
    assert result.output.strip() == "x2 M L' (z' S2 R)"
