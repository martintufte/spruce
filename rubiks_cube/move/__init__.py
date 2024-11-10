import re

from rubiks_cube.utils.formatting import format_string


def strip_move(move: str) -> str:
    """Strip a decorated move of parentheses and slashes.

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


def is_valid_moves(moves: list[str]) -> bool:
    """Check if a list of moves uses valid Rubik's Cube notation.

    Args:
        moves (list[str]): List of moves.

    Returns:
        bool: True if the moves are valid.
    """

    pattern = r"^[I]?$|^[3456789]?[RLFBUD][w][2']?$|^[RLUDFBxyzMES][2']?$"
    return all(re.match(pattern, strip_move(move)) for move in moves)


def format_string_to_moves(string: str) -> list[str]:
    """Format a string into a list of moves.

    Args:
        string (str): Raw string.

    Raises:
        ValueError: Invalid moves entered.

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

    if is_valid_moves(moves):
        return moves

    raise ValueError(f"Invalid moves! got {moves}")


def format_string_to_generator(gen_string: str) -> list[list[str]]:
    """Format a string into a set of moves.

    Args:
        gen_string (str): String to format.

    Raises:
        ValueError: Invalid move generator format.

    Returns:
        list[list[str]]: List of list of valid moves.
    """

    gen_string = gen_string.strip()
    assert gen_string.startswith("<") and gen_string.endswith(">"), "Invalid move generator format!"
    string_moves = gen_string[1:-1].split(",")

    generator = [format_string_to_moves(string) for string in string_moves]

    return generator
