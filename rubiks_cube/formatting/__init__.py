from rubiks_cube.formatting.move import decorate_move
from rubiks_cube.formatting.move import is_valid_moves
from rubiks_cube.formatting.move import strip_move
from rubiks_cube.formatting.string import format_string


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
    if not gen_string.startswith("<") and gen_string.endswith(">"):
        raise ValueError("Invalid move generator format!")
    string_moves = gen_string[1:-1].split(",")

    generator = [format_string_to_moves(string) for string in string_moves]

    return generator
