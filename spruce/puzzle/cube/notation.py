"""Cube move notation: expanding compound symbols and parsing sequences."""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any

from spruce.configuration.regex import SLICE_PATTERN
from spruce.configuration.regex import WIDE_PATTERN
from spruce.move.sequence import MoveSequence
from spruce.types import MoveSymbol

if TYPE_CHECKING:
    import re

    from spruce.algebra.meta import MoveMeta


def substitute_slice_move(symbol: MoveSymbol) -> tuple[MoveSymbol, ...]:
    """Substitute the slice symbol, returning the word it expands to."""
    # Keyed by the bare slice letter; the parts are glued to a turn modifier below,
    # so they are notation fragments rather than standalone move symbols.
    slice_mapping: dict[str, tuple[str, str, str]] = {
        "M": ("L'", "R", "x'"),
        "E": ("U", "D'", "y'"),
        "S": ("F'", "B", "z"),
    }

    def replace_match(match: re.Match[Any]) -> str:
        slice = match.group(1)
        turn_mod = match.group(2)
        first, second, rot = slice_mapping[slice]

        combined = f"{first}{turn_mod} {second}{turn_mod} {rot}{turn_mod}"
        return combined.replace("''", "").replace("'2", "2")

    substituted = SLICE_PATTERN.sub(replace_match, symbol)

    return tuple(MoveSymbol(part) for part in substituted.split())


# TODO: Consider removing hardcoded wide substitution
def substitute_wide_move(symbol: MoveSymbol, cube_size: int) -> tuple[MoveSymbol, ...]:
    """Substitute the wide notation if wider than cube_size/2, as the word it expands to."""
    # Keyed by the bare face letter; the parts are glued to width and turn modifiers
    # below, so they are notation fragments rather than standalone move symbols.
    wide_mapping: dict[str, tuple[str, str, str]] = {
        "L": ("R", "x", "'"),
        "R": ("L", "x", ""),
        "F": ("B", "z", ""),
        "B": ("F", "z", "'"),
        "U": ("D", "y", ""),
        "D": ("U", "y", "'"),
    }

    def replace_match(match: re.Match[Any]) -> str:
        wide = match.group(1) or "2"
        diff = cube_size - int(wide)
        if diff >= cube_size / 2:
            return match.group(0)

        wide_mod = "w" if diff > 1 else ""
        diff_mod = str(diff) if diff > 2 else ""
        turn_mod = match.group(3)
        move = match.group(2)
        base, rot, rot_mod = wide_mapping[move]
        rot_mod = f"{rot_mod}{turn_mod}".replace("''", "").replace("'2", "2")

        if diff < 1:
            return f"{rot}{rot_mod}"
        return f"{diff_mod}{base}{wide_mod}{turn_mod} {rot}{rot_mod}"

    substituted = WIDE_PATTERN.sub(replace_match, symbol)

    return tuple(MoveSymbol(part) for part in substituted.split())


def parse_sequence(string: str, move_meta: MoveMeta) -> MoveSequence:
    """Parse a move sequence and validate its symbols against the group.

    `MoveSequence.from_str` only checks that the notation is well formed; this also
    checks that every symbol exists in the group.

    Raises:
        ValueError: If the string is not a well formed sequence of this group.
    """
    sequence = MoveSequence.from_str(string)
    move_meta.to_word([*sequence.normal, *sequence.inverse])

    return sequence
