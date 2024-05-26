import re


def is_valid_moves(moves: list[str]) -> bool:
    """Check if a list of moves is valid Rubik's Cube notation."""

    pattern = r"^[RLFBUD][w][2']?$|^[RLUDFBxyzMES][2']?$"

    return all(re.match(pattern, strip_move(move)) for move in moves)


def string_to_moves(input_string: str) -> list[str]:
    """Split a string into moves."""

    moves = []
    niss = False
    for move in input_string.split():
        stripped_move = strip_move(move)
        if move.startswith("("):
            niss = not niss
        moves.append("(" + stripped_move + ")" if niss else stripped_move)
        if move.endswith(")"):
            niss = not niss

    if is_valid_moves(moves):
        return moves
    else:
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
    """Return a representation of the move."""

    return " ".join(moves).replace(") (", " ").strip()


def niss_move(move: str) -> str:
    """
    Niss a move. Eg.
    R -> (R)
    (R) -> R
    """
    if move.startswith("("):
        return move.replace("(", "").replace(")", "")
    return "(" + move + ")"


def is_rotation(move: str) -> bool:
    """Return True if the move is a rotation."""

    return move in {" ", "x", "x'", "x2", "y", "y'", "y2", "z", "z'", "z2"}


def apply_rotation(move: str, rotation: str) -> str:
    """Apply a rotation to the move."""
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
    if move.startswith("F") or move.startswith("B"):
        return "F/B"
    elif move.startswith("R") or move.startswith("L"):
        return "R/L"
    elif move.startswith("U") or move.startswith("D"):
        return "U/D"

    return None


def main() -> None:
    formatted_string = "(Fw R2 x) U2 M' (L2 Rw2 F2) Bw y' D' F'"

    print("Formatted input:", formatted_string)

    moves = string_to_moves(formatted_string)

    print("Moves:", moves)


if __name__ == "__main__":
    main()
