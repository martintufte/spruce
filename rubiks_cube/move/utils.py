from __future__ import annotations

import re

from rubiks_cube.formatting.regex import ROTATION_SEARCH
from rubiks_cube.formatting.regex import SINGLE_PATTERN
from rubiks_cube.formatting.regex import WIDE_PATTERN


def turn_to_int(turn: str) -> int:
    """Convert turn notation to integer representation.

    Args:
        turn (str): Turn notation ("2", "'", or empty string).

    Returns:
        int: Integer representation of the turn.
    """
    return {"2": 2, "'": 3}.get(turn, 1)


def move_to_coord(move: str) -> tuple[str, int, int]:
    """Return the face, number of layers being turned and the number of quarter turns.

    Args:
        move (str): The move.

    Raises:
        ValueError: If the format is wrong.

    Returns:
        tuple[str, int, int]: The face, how many layers to turn, quarter turns.
    """
    if match := re.match(SINGLE_PATTERN, move):
        return match.group(1), 1, turn_to_int(match.group(2))
    if match := re.match(WIDE_PATTERN, move):
        return match.group(2), int(match.group(1) or "2"), turn_to_int(match.group(3))
    raise ValueError("Move does not have the expected format!")


def coord_to_move(face: str, wide_mod: int, turn_mod: int) -> str:
    """
    Return the string representation of the tuple.

    Args:
        face (str): The face.
        wide_mod (int): The number of layers being turned.
        turn_mod (int): The number of quarter turns.

    Returns:
        str: String representation.

    Examples:
        >>> coord_to_move("R", 1, 1)
        'R'
        >>> coord_to_move("R", 2, 3)
        "Rw'"
        >>> coord_to_move("D", 3, 2)
        "3Dw2"
        >>> coord_to_move("R", 1, 3)
    """
    wide = str(wide_mod) if wide_mod > 2 else ""
    turn = [None, "", "2", "'"][turn_mod % 4]
    if turn is None:
        return ""
    if wide_mod > 1:
        face += "w"
    return f"{wide}{face}{turn}"


def get_axis(move: str) -> str | None:
    """Get the axis of a move."""
    if "F" in move or "B" in move:
        return "z"
    if "L" in move or "R" in move:
        return "x"
    if "U" in move or "D" in move:
        return "y"
    return None


def simplyfy_axis_moves(moves: list[str]) -> list[str]:
    """Combine adjacent moves if they cancel each other."""
    coords = [move_to_coord(move) for move in moves]

    # Group by (face, wide) and sum the turns
    groups: dict[tuple[str, int], int] = {}
    for face, wide, turn in coords:
        key = (face, wide)
        groups[key] = groups.get(key, 0) + turn

    # Sort groups by face and wide modifier to match pandas behavior
    return_list = []
    for face, wide in sorted(groups.keys()):
        total_turn = groups[(face, wide)]
        grouped_move = coord_to_move(face, wide, total_turn)
        if grouped_move != "":
            return_list.append(grouped_move)

    return return_list


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


def is_slashed(move: str) -> bool:
    """Check if the move is slashed.

    Args:
        move (str): Move to check.

    Returns:
        bool: Whether the move is slashed.
    """
    return "~" in move


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


def slash_move(move: str) -> str:
    if is_niss(move):
        if is_slashed(move):
            return "(" + move[2:-2] + ")"
        return "(~" + move[1:-1] + "~)"
    if is_slashed(move):
        return move[1:-1]
    return "~" + move + "~"


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
        "i": {},
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
    """Collapse rotations in a sequence to a standard rotation.

    It rotates the cube to correct up-face and the correct front-face.

    Args:
        rotation_list (list[str]): List of rotations.

    Returns:
        list[str]: List of standard rotations.
    """
    standard_rotations = {
        "UF": "",
        "UL": "y'",
        "UB": "y2",
        "UR": "y",
        "FU": "x y2",
        "FL": "x y'",
        "FD": "x",
        "FR": "x y",
        "RU": "z' y'",
        "RF": "z'",
        "RD": "z' y",
        "RB": "z' y2",
        "BU": "x'",
        "BL": "x' y'",
        "BD": "x' y2",
        "BR": "x' y",
        "LU": "z y",
        "LF": "z",
        "LD": "z y'",
        "LB": "z y2",
        "DF": "z2",
        "DL": "x2 y'",
        "DB": "x2",
        "DR": "x2 y",
    }
    transition_dict = {
        "x": {
            "UF": "FD",
            "UL": "LD",
            "UB": "BD",
            "UR": "RD",
            "FU": "UB",
            "FL": "LB",
            "FD": "DB",
            "FR": "RB",
            "RU": "UL",
            "RF": "FL",
            "RD": "DL",
            "RB": "BL",
            "BU": "UF",
            "BL": "LF",
            "BD": "DF",
            "BR": "RF",
            "LU": "UR",
            "LF": "FR",
            "LD": "DR",
            "LB": "BR",
            "DF": "FU",
            "DL": "LU",
            "DB": "BU",
            "DR": "RU",
        },
        "x'": {
            "UF": "BU",
            "UL": "RU",
            "UB": "FU",
            "UR": "LU",
            "FU": "DF",
            "FL": "RF",
            "FD": "UF",
            "FR": "LF",
            "RU": "DR",
            "RF": "BR",
            "RD": "UR",
            "RB": "FR",
            "BU": "DB",
            "BL": "RB",
            "BD": "UB",
            "BR": "LB",
            "LU": "DL",
            "LF": "BL",
            "LD": "UL",
            "LB": "FL",
            "DF": "BD",
            "DL": "RD",
            "DB": "FD",
            "DR": "LD",
        },
        "x2": {
            "UF": "DB",
            "UL": "DR",
            "UB": "DF",
            "UR": "DL",
            "FU": "BD",
            "FL": "BR",
            "FD": "BU",
            "FR": "BL",
            "RU": "LD",
            "RF": "LB",
            "RD": "LU",
            "RB": "LF",
            "BU": "FD",
            "BL": "FR",
            "BD": "FU",
            "BR": "FL",
            "LU": "RD",
            "LF": "RB",
            "LD": "RU",
            "LB": "RF",
            "DF": "UB",
            "DL": "UR",
            "DB": "UF",
            "DR": "UL",
        },
        "y": {
            "UF": "UR",
            "UL": "UF",
            "UB": "UL",
            "UR": "UB",
            "FU": "FL",
            "FL": "FD",
            "FD": "FR",
            "FR": "FU",
            "RU": "RF",
            "RF": "RD",
            "RD": "RB",
            "RB": "RU",
            "BU": "BR",
            "BL": "BU",
            "BD": "BL",
            "BR": "BD",
            "LU": "LB",
            "LF": "LU",
            "LD": "LF",
            "LB": "LD",
            "DF": "DL",
            "DL": "DB",
            "DB": "DR",
            "DR": "DF",
        },
        "y'": {
            "UF": "UL",
            "UL": "UB",
            "UB": "UR",
            "UR": "UF",
            "FU": "FR",
            "FL": "FU",
            "FD": "FL",
            "FR": "FD",
            "RU": "RB",
            "RF": "RU",
            "RD": "RF",
            "RB": "RD",
            "BU": "BL",
            "BL": "BD",
            "BD": "BR",
            "BR": "BU",
            "LU": "LF",
            "LF": "LD",
            "LD": "LB",
            "LB": "LU",
            "DF": "DR",
            "DL": "DF",
            "DB": "DL",
            "DR": "DB",
        },
        "y2": {
            "UF": "UB",
            "UL": "UR",
            "UB": "UF",
            "UR": "UL",
            "FU": "FD",
            "FL": "FR",
            "FD": "FU",
            "FR": "FL",
            "RU": "RD",
            "RF": "RB",
            "RD": "RU",
            "RB": "RF",
            "BU": "BD",
            "BL": "BR",
            "BD": "BU",
            "BR": "BL",
            "LU": "LD",
            "LF": "LB",
            "LD": "LU",
            "LB": "LF",
            "DF": "DB",
            "DL": "DR",
            "DB": "DF",
            "DR": "DL",
        },
        "z": {
            "UF": "LF",
            "UL": "BL",
            "UB": "RB",
            "UR": "FR",
            "FU": "RU",
            "FL": "UL",
            "FD": "LD",
            "FR": "DR",
            "RU": "BU",
            "RF": "UF",
            "RD": "FD",
            "RB": "DB",
            "BU": "LU",
            "BL": "DL",
            "BD": "RD",
            "BR": "UR",
            "LU": "FU",
            "LF": "DF",
            "LD": "BD",
            "LB": "UB",
            "DF": "RF",
            "DL": "FL",
            "DB": "LB",
            "DR": "BR",
        },
        "z'": {
            "UF": "RF",
            "UL": "FL",
            "UB": "LB",
            "UR": "BR",
            "FU": "LU",
            "FL": "DL",
            "FD": "RD",
            "FR": "UR",
            "RU": "FU",
            "RF": "DF",
            "RD": "BD",
            "RB": "UB",
            "BU": "RU",
            "BL": "UL",
            "BD": "LD",
            "BR": "DR",
            "LU": "BU",
            "LF": "UF",
            "LD": "FD",
            "LB": "DB",
            "DF": "LF",
            "DL": "BL",
            "DB": "RB",
            "DR": "FR",
        },
        "z2": {
            "UF": "DF",
            "UL": "DL",
            "UB": "DB",
            "UR": "DR",
            "FU": "BU",
            "FL": "BL",
            "FD": "BD",
            "FR": "BR",
            "RU": "LU",
            "RF": "LF",
            "RD": "LD",
            "RB": "LB",
            "BU": "FU",
            "BL": "FL",
            "BD": "FD",
            "BR": "FR",
            "LU": "RU",
            "LF": "RF",
            "LD": "RD",
            "LB": "RB",
            "DF": "UF",
            "DL": "UL",
            "DB": "UB",
            "DR": "UR",
        },
    }

    current_state = "UF"
    for rotation in rotation_list:
        current_state = transition_dict[rotation][current_state]

    standard_rotation_list = standard_rotations[current_state]

    return standard_rotation_list.split()
