import re

from rubiks_cube.formatting.decorator import decorate_move
from rubiks_cube.formatting.decorator import strip_move
from rubiks_cube.formatting.regex import MOVE_REGEX
from rubiks_cube.formatting.string import format_string


def format_string_to_moves(string: str) -> list[str]:
    """
    Format a string into a list of moves.

    Args:
        string (str): Raw string.

    Raises:
        ValueError: Could not format string to moves.

    Returns:
        list[str]: List of valid moves.

    """
    formatted_string = format_string(string)

    moves = []
    niss = False
    slash = False
    for move in formatted_string.split():
        if move.startswith("("):
            niss = not niss
        if move.startswith("~"):
            slash = not slash

        stripped_move = strip_move(move)
        moves.append(decorate_move(stripped_move, niss, slash))

        if move.endswith(")"):
            niss = not niss
        if move.endswith("~"):
            slash = not slash

    if all(re.match(MOVE_REGEX, strip_move(move)) for move in moves):
        return moves

    raise ValueError(f"Could not format string to moves. Got: {moves}")
