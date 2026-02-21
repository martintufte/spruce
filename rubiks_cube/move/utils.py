from __future__ import annotations

import re

from rubiks_cube.configuration.regex import ROTATION_SEARCH
from rubiks_cube.move.rotation_magic import IDENTITY_ROTATION_STATE
from rubiks_cube.move.rotation_magic import ROTATION_SOLUTIONS
from rubiks_cube.move.rotation_magic import ROTATION_TRANSITION_TABLE


def is_rotation(move: str) -> bool:
    """Return True if the move is a rotation.

    Args:
        move (str): Move to check.

    Returns:
        bool: True if the move is a rotation.
    """
    return bool(re.search(ROTATION_SEARCH, move))


def is_niss(move: str) -> bool:
    """Check if the move is a NISS move.

    Args:
        move (str): Move to check.

    Returns:
        bool: Whether the move is a NISS move.
    """
    return move.startswith("(") and move.endswith(")")


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


def niss_move(move: str) -> str:
    if is_niss(move):
        return move[1:-1]
    return "(" + move + ")"


def rotate_move(move: str, rotation: str) -> str:
    """Apply a rotation by mapping the move to the new move.

    Args:
        move (str): Move to rotate.
        rotation (str): Rotation to apply.

    Returns:
        str: Rotated move.
    """
    assert is_rotation(rotation), f"Rotation {rotation} must be a rotation!"
    rotation_moves_dict: dict[str, dict[str, str]] = {
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
    face = move[0]
    new_face = rotation_moves_dict[rotation].get(face, face)

    return move.replace(face, new_face)


def combine_rotations(rotation_list: list[str]) -> list[str]:
    """Collapse rotations in a sequence to a standard rotations.

    Args:
        rotation_list (list[str]): List of rotations.

    Returns:
        list[str]: List of standard rotations.
    """

    current_state = IDENTITY_ROTATION_STATE
    for rotation in rotation_list:
        current_state = ROTATION_TRANSITION_TABLE[rotation][current_state]

    return ROTATION_SOLUTIONS[current_state]


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
