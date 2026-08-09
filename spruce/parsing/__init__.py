from __future__ import annotations

from typing import TYPE_CHECKING

from spruce.move.formatting import is_valid_symbols
from spruce.move.formatting import replace_confusing_chars
from spruce.move.formatting import strip_comments
from spruce.move.sequence import MoveSequence
from spruce.types import MoveSymbol

if TYPE_CHECKING:
    from collections.abc import Set as AbstractSet

    from spruce.move.meta import MoveMeta


def parse_generator(user_input: str) -> frozenset[MoveSymbol]:
    """Parse a move generator string like "<U, R, F>" into a set of move symbols."""
    text = replace_confusing_chars(strip_comments(user_input)).strip()

    if not (text.startswith("<") and text.endswith(">")):
        raise ValueError("Invalid move generator format!")

    symbols = frozenset(
        MoveSymbol(symbol.strip()) for symbol in text[1:-1].split(",") if symbol.strip()
    )

    if symbols and not is_valid_symbols(" ".join(symbols)):
        raise ValueError("Invalid symbols entered!")

    return symbols


def format_generator(generator: AbstractSet[MoveSymbol], move_meta: MoveMeta) -> str:
    """Format a set of move symbols as a move generator string like "<U, R, F>"."""
    return "<" + ", ".join(move_meta.sorted(generator)) + ">"


def parse_scramble(raw_scramble: str) -> MoveSequence:
    """Parse a scramble and return the move sequence."""
    raw_scramble = replace_confusing_chars(strip_comments(raw_scramble))

    if not is_valid_symbols(raw_scramble):
        raise ValueError("Invalid symbols entered!")

    scramble = MoveSequence.from_str(raw_scramble)

    if scramble.inverse:
        raise ValueError("Inverse moves for scramble is not supported")

    return scramble


def parse_steps(user_input: str) -> list[MoveSequence]:
    """Parse user input lines.

    This parser intentionally supports only plain move lines.
    Definitions/substitutions/skeleton syntax are rejected.
    """
    steps: list[MoveSequence] = []
    for line_number, raw_line in enumerate(user_input.splitlines(), start=1):
        line = replace_confusing_chars(strip_comments(raw_line)).strip()
        if not line:
            continue

        if any(token in line for token in ("=", "[", "]", "->", "*", ";")):
            raise ValueError(
                f"Definitions, substitutions, and skeleton syntax are not supported at line "
                f"{line_number}.",
            )

        if not is_valid_symbols(line):
            raise ValueError(f"Invalid symbols entered at line {line_number}.")

        try:
            steps.append(MoveSequence.from_str(line))
        except ValueError as exc:
            raise ValueError(f"Invalid moves entered at line {line_number}.") from exc

    return steps
