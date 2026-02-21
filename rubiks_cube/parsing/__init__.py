from __future__ import annotations

from rubiks_cube.move.formatting import is_valid_symbols
from rubiks_cube.move.formatting import replace_confusing_chars
from rubiks_cube.move.formatting import strip_comments
from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.move.steps import MoveSteps


def parse_scramble(raw_scramble: str) -> MoveSequence:
    """Parse a scramble and return the move sequence."""
    raw_scramble = replace_confusing_chars(strip_comments(raw_scramble))

    if not is_valid_symbols(raw_scramble):
        raise ValueError("Invalid symbols entered!")

    scramble = MoveSequence.from_str(raw_scramble)

    if scramble.inverse:
        raise ValueError("Inverse moves for scramble is not supported")

    return scramble


def parse_steps(user_input: str) -> MoveSteps:
    """Parse user input lines.

    This parser intentionally supports only plain move lines.
    Definitions/substitutions/skeleton syntax are rejected.
    """
    steps: list[MoveSequence] = []
    for line_number, raw_line in enumerate(user_input.splitlines(), start=1):
        line = replace_confusing_chars(strip_comments(raw_line)).strip()
        if not line:
            continue

        if any(token in line for token in ("=", "[", "]", "->")):
            raise ValueError(
                f"Definitions, substitutions, and skeleton syntax are not supported at line "
                f"{line_number}."
            )

        if not is_valid_symbols(line):
            raise ValueError(f"Invalid symbols entered at line {line_number}.")

        try:
            steps.append(MoveSequence.from_str(line))
        except ValueError as exc:
            raise ValueError(f"Invalid moves entered at line {line_number}.") from exc

    return MoveSteps(steps)
