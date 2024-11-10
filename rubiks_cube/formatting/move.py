import re


def is_valid_moves(moves: list[str]) -> bool:
    """Check if a list of moves uses valid Rubik's Cube notation.

    Args:
        moves (list[str]): List of moves.

    Returns:
        bool: True if the moves are valid.
    """

    pattern = r"^[I]?$|^[3456789]?[RLFBUD][w][2']?$|^[RLUDFBxyzMES][2']?$"
    return all(re.match(pattern, strip_move(move)) for move in moves)


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
    if move.startswith("~"):
        move = move[1:]
    if move.endswith("~"):
        move = move[:-1]
    return move


def undecorate_move(move: str) -> tuple[str, bool, bool]:
    """Undecorate a move with parentheses and slashes.

    Args:
        move (str): Move to unstrip.

    Returns:
        tuple[str, bool, bool]: Unstripped move, niss, slash.
    """
    niss = False
    slash = False
    if move.startswith("(") and move.endswith(")"):
        niss = True
        move = move[1:-1]
    if move.startswith("~") and move.endswith("~"):
        slash = True
        move = move[1:-1]
    return move, niss, slash


def decorate_move(move: str, niss: bool = False, slash: bool = False) -> str:
    """Decorate a move with parentheses and slashes.

    Args:
        move (str): Move to unstrip.
        niss (bool): True if niss is active.
        slash (bool): True if slash is active.

    Returns:
        str: Unstripped move.
    """
    if slash:
        move = "~" + move + "~"
    if niss:
        move = "(" + move + ")"
    return move
