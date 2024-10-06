import re

from rubiks_cube.utils.formatting import format_string


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
    for move in formatted_string.split():
        stripped_move = strip_move(move)
        if move.startswith("("):
            niss = not niss
        moves.append("(" + stripped_move + ")" if niss else stripped_move)
        if move.endswith(")"):
            niss = not niss

    if is_valid_moves(moves):
        return moves
    raise ValueError(f"Invalid moves entered! got {moves}")


def is_valid_moves(moves: list[str]) -> bool:
    """Check if a list of moves uses valid Rubik's Cube notation.

    Args:
        moves (list[str]): List of moves.

    Returns:
        bool: True if the moves are valid.
    """

    pattern = r"^[I]?$|^[23456789]?[RLFBUD][w][2']?$|^[RLUDFBxyzMES][2']?$"
    return all(re.match(pattern, strip_move(move)) for move in moves)


def invert_move(move: str) -> str:
    """Invert a move.

    Args:
        move (str): Move to invert.

    Returns:
        str: Inverted move.
    """
    if move.startswith("("):
        return "(" + invert_move(move[1:-1]) + ")"
    if move.endswith("'"):
        return move[:-1]
    elif move.endswith("2"):
        return move
    return move + "'"


def strip_move(move: str) -> str:
    """Strip a move of parentheses.

    Args:
        move (str): Move to strip.

    Returns:
        str: Stripped move.
    """
    return move.replace("(", "").replace(")", "")


def is_rotation(move: str) -> bool:
    """Return True if the move is a rotation.

    Args:
        move (str): Move to check.

    Returns:
        bool: True if the move is a rotation.
    """

    return bool(re.search("[ixyz]", move))


def rotate_move(move: str, rotation: str) -> str:
    """Apply a rotation by mapping the move to the new move.

    Args:
        move (str): Move to rotate.
        rotation (str): Rotation to apply.

    Returns:
        str: Rotated move.
    """
    assert is_rotation(rotation), f"Rotation {rotation} must be a rotation!"
    rotation_moves_dict = {
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

    generator = []
    for string in string_moves:
        moves = format_string_to_moves(string)
        if is_valid_moves(moves):
            generator.append(moves)
        else:
            raise ValueError(f"Invalid moves for generator! got {moves}")

    return generator
