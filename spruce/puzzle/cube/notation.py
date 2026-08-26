"""Cube move notation: the patterns, expanding compound symbols, and parsing sequences."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING
from typing import Any
from typing import Final

from spruce.algebra.sequence import MoveSequence
from spruce.puzzle.cube.formatting import format_string
from spruce.puzzle.cube.formatting import strip_move
from spruce.types import MoveSymbol

if TYPE_CHECKING:
    from spruce.algebra.meta import MoveMeta


MOVE_REGEX: Final[str] = r"^[Ii]?$|^[3456789]?[LRFBUD][w][2']?$|^[LRFBUDxyzMES][2']?$"

IDENTITY_PATTERN: Final[re.Pattern[str]] = re.compile(r"^[Ii]?$")
SINGLE_PATTERN: Final[re.Pattern[str]] = re.compile(r"^([LRFBUD])([2']?)$")
WIDE_PATTERN: Final[re.Pattern[str]] = re.compile(r"^([3456789]?)([LRFBUD])w([2']?)$")
SLICE_PATTERN: Final[re.Pattern[str]] = re.compile(r"^([MES])([2']?)$")
ROTATION_PATTERN: Final[re.Pattern[str]] = re.compile(r"^([xyz])([2']?)$")

IDENTITY_SEARCH: Final[re.Pattern[str]] = re.compile(r"[Ii]")
WIDE_SEARCH: Final[re.Pattern[str]] = re.compile(r"[LRFBUD]w")
SLICE_SEARCH: Final[re.Pattern[str]] = re.compile(r"[MES]")
ROTATION_SEARCH: Final[re.Pattern[str]] = re.compile(r"[xyz]")
DOUBLE_SEARCH: Final[re.Pattern[str]] = re.compile(r"[2]")
DOUBLE_SLICE_SEARCH: Final[re.Pattern[str]] = re.compile(r"[MES]2")
DOUBLE_ROTATION_SEARCH: Final[re.Pattern[str]] = re.compile(r"[xyz]2")


def canonical_key(move: str) -> tuple[int, int, int, int]:
    """Get the canonical key for a Rubik's Cube move.

    Args:
        move (str): The move notation (e.g., "R", "U2", "M'", etc.).

    Raises:
        ValueError: If the move is invalid.

    Returns:
        tuple[int, int, int, int]: A tuple representing the move's canonical form.
    """
    if match := SINGLE_PATTERN.match(move):
        return (0, "LRFBUD".index(match.group(1)), " 2'".index(match.group(2) or " "), 0)

    if match := WIDE_PATTERN.match(move):
        return (
            1,
            int(match.group(1) or 2),
            "LRFBUD".index(match.group(2)),
            " 2'".index(match.group(3) or " "),
        )

    if match := SLICE_PATTERN.match(move):
        return (2, "MES".index(match.group(1)), " 2'".index(match.group(2) or " "), 0)

    if match := ROTATION_PATTERN.match(move):
        return (3, "ixyz".index(match.group(1)), " 2'".index(match.group(2) or " "), 0)

    raise ValueError(f"Invalid move: {move}")


# TODO: Consider removing hardcoded slice substitutions
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

    `parse_moves` only checks that the notation is well formed; this also
    checks that every symbol exists in the group.

    Raises:
        ValueError: If the string is not a well formed sequence of this group.
    """
    sequence = parse_moves(string)
    move_meta.to_word([*sequence.normal, *sequence.inverse])

    return sequence


def parse_moves(string: str) -> MoveSequence:
    """Parse cube notation into a sequence, without checking it against any group.

    Symbols in parentheses go on the inverse side (NISS notation).

    Raises:
        ValueError: If the string is not well formed cube notation.
    """
    formatted_string = format_string(string)

    normal: list[MoveSymbol] = []
    inverse: list[MoveSymbol] = []
    niss = False
    for move in formatted_string.split():
        if move.startswith("("):
            niss = not niss

        symbol = MoveSymbol(strip_move(move))

        if not re.match(MOVE_REGEX, symbol):
            raise ValueError(f"Could not format string to moves. Got: {symbol}")

        if niss:
            inverse.append(symbol)
        else:
            normal.append(symbol)

        if move.endswith(")"):
            niss = not niss

    return MoveSequence(normal=normal, inverse=inverse)
