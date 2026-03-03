from __future__ import annotations

import re

from rubiks_cube.configuration.regex import ROTATION_SEARCH

ROTATION_FACE_MAPS: dict[str, dict[str, str]] = {
    "x": {"F": "D", "D": "B", "B": "U", "U": "F"},
    "x'": {"F": "U", "U": "B", "B": "D", "D": "F"},
    "x2": {"F": "B", "U": "D", "B": "F", "D": "U"},
    "y": {"F": "R", "L": "F", "B": "L", "R": "B"},
    "y'": {"F": "L", "L": "B", "B": "R", "R": "F"},
    "y2": {"F": "B", "L": "R", "B": "F", "R": "L"},
    "z": {"U": "L", "R": "U", "D": "R", "L": "D"},
    "z'": {"U": "R", "R": "D", "D": "L", "L": "U"},
    "z2": {"U": "D", "R": "L", "D": "U", "L": "R"},
}


def is_rotation(move: str) -> bool:
    """Return True if the move is a rotation.

    Args:
        move (str): Move to check.

    Returns:
        bool: True if the move is a rotation.
    """
    return bool(re.search(ROTATION_SEARCH, move))


def invert_move(move: str) -> str:
    """Invert a move.

    Args:
        move (str): Move to invert.

    Returns:
        str: Inverted move.
    """
    if move.endswith("2"):
        return move
    return move[:-1] if move.endswith("'") else move + "'"


def rotate_move(move: str, rotation: str) -> str:
    """Apply a rotation by mapping the move to the new move.

    Args:
        move (str): Move to rotate.
        rotation (str): Rotation to apply.

    Returns:
        str: Rotated move.
    """
    assert is_rotation(rotation), f"Rotation {rotation} must be a rotation!"
    face = move[0]

    return move.replace(face, ROTATION_FACE_MAPS[rotation].get(face, face))


def strip_move(move: str) -> str:
    """Strip a move of parenthesis.

    Args:
        move (str): Move to strip.

    Returns:
        str: Stripped move without NISS notation.
    """
    if move.startswith("("):
        move = move[1:]
    if move.endswith(")"):
        move = move[:-1]
    return move


def unstrip_move(move: str) -> str:
    """Decorate a move with parentheses.

    Args:
        move (str): Move to unstrip.

    Returns:
        str: Unstripped move with NISS notation.
    """
    if not move.startswith("("):
        move = "(" + move
    if not move.endswith(")"):
        move = move + ")"
    return move
