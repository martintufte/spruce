import re


def is_valid_moves(moves: list[str]) -> bool:
    """
    Check if a list of moves uses valid Rubik's Cube notation.
    """

    pattern = r"^[I]?$|^[RLFBUD][w][2']?$|^[RLUDFBxyzMES][2']?$"

    return all(re.match(pattern, strip_move(move)) for move in moves)


def string_to_moves(formatted_string: str) -> list[str]:
    """
    Split a formatted string into a list moves.
    """

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
    raise ValueError("Invalid moves entered!")


def invert_move(move: str) -> str:
    """Invert a move."""

    if move.endswith("'"):
        return move[:-1]
    elif move.endswith("2"):
        return move
    return move + "'"


def strip_move(move: str) -> str:
    """Strip a move of parentheses."""

    return move.replace("(", "").replace(")", "")


def repr_moves(moves: list[str]) -> str:
    """Return a representation of the moves."""

    return " ".join(moves).replace(") (", " ")


def niss_move(move: str) -> str:
    """
    Niss a move.
    E.g. R -> (R), (R) -> R
    """
    if move.startswith("("):
        return move.replace("(", "").replace(")", "")
    return "(" + move + ")"


def is_rotation(move: str) -> bool:
    """Return True if the move is a rotation."""

    return move in {" ", "x", "x'", "x2", "y", "y'", "y2", "z", "z'", "z2"}


def rotate_move(move: str, rotation: str) -> str:
    """Apply a rotation by mapping the move to the new move."""
    assert is_rotation(rotation), f"Rotation {rotation} must be a rotation!"
    rotation_moves_dict = {
        " ": {},
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


def get_axis(move: str) -> str | None:
    """Get the axis of a move."""
    if move[0] in "FB":
        return "z"
    elif move[0] in "RL":
        return "x"
    elif move[0] in "UD":
        return "y"
    return None


def move_as_int(move: str) -> int:
    """Return the integer representation of a move."""
    if move.endswith("2"):
        return 2
    elif move.endswith("'"):
        return -1
    return 1


def main() -> None:
    formatted_string = "(Fw x R2) U2 M' (L' Dw2 F2) Bw y' F'"
    moves = string_to_moves(formatted_string)
    print("Formatted input:", formatted_string)
    print("Moves:", moves)


if __name__ == "__main__":
    main()
