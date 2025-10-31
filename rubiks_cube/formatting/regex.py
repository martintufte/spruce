from __future__ import annotations

import re
from typing import Final

MOVE_REGEX: Final[str] = r"^[Ii]?$|^[3456789]?[LRFBUD][w][2']?$|^[LRFBUDxyzMES][2']?$"

SINGLE_PATTERN: Final[re.Pattern[str]] = re.compile(r"^([LRFBUD])([2']?)$")
WIDE_PATTERN: Final[re.Pattern[str]] = re.compile(r"^([3456789]?)([LRFBUD])w([2']?)$")
SLICE_PATTERN: Final[re.Pattern[str]] = re.compile(r"^([MES])([2']?)$")
ROTATION_PATTERN: Final[re.Pattern[str]] = re.compile(r"^([ixyz])([2']?)$")

SLICE_SEARCH: Final[re.Pattern[str]] = re.compile(r"[MES]")
ROTATION_SEARCH: Final[re.Pattern[str]] = re.compile(r"[ixyz]")
DOUBLE_SEARCH: Final[re.Pattern[str]] = re.compile(r"[2]")
DOUBLE_SLICE_SEARCH: Final[re.Pattern[str]] = re.compile(r"[MES]2")
DOUBLE_ROTATION_SEARCH: Final[re.Pattern[str]] = re.compile(r"[ixyz]2")


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
