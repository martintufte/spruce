from __future__ import annotations


def strip_move(move: str) -> str:
    """Strip a decorated move.

    Args:
        move (str): Move to strip.

    Returns:
        str: Stripped move.
    """
    if move.startswith("("):
        move = move[1:]
    if move.endswith(")"):
        move = move[:-1]
    return move


def undecorate_move(move: str) -> tuple[str, bool]:
    """Undecorate a move with parentheses.

    Args:
        move (str): Move to unstrip.

    Returns:
        tuple[str, bool]: Unstripped move, niss.
    """
    niss = False
    if move.startswith("(") and move.endswith(")"):
        niss = True
        move = move[1:-1]
    return move, niss


def decorate_move(move: str, niss: bool = False) -> str:
    """Decorate a move with parentheses.

    Args:
        move (str): Move to unstrip.
        niss (bool): True if niss is active.

    Returns:
        str: Unstripped move.
    """
    if niss:
        move = "(" + move + ")"
    return move
