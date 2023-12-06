import re


def is_valid_symbols(input_string: str, additional_chars: str = "") -> bool:
    """Check that a string only contains valid symbols."""
    valid_chars = "RLFBUDMESrlfbudxyzw23' ()/\t\n" + additional_chars
    return all(char in valid_chars for char in input_string)


def split_into_moves_comment(input_string: str) -> tuple[str, str]:
    """Split a sequence into moves and comment."""

    # Find the comment and split the string
    idx = input_string.find("//")
    if idx > 0:
        return input_string[:idx], input_string[(idx+2):]
    return input_string, ""


def remove_redundant_parenteses(input_string: str) -> str:
    """Remove redundant moves in a sequence."""

    # Remove redundant parentheses
    output_string = input_string
    while True:
        output_string = re.sub(r"\(\s*\)", "", output_string)
        output_string = re.sub(r"\)\s*\(", "", output_string)
        if output_string == input_string:
            break
        input_string = output_string

    return output_string


def format_wide_notation(input_string: str):
    """Replace old wide notation with new wide notation."""
    replace_dict = {
        "u": "Uw", "d": "Dw", "f": "Fw", "b": "Bw", "l": "Lw", "r": "Rw",
    }
    for old, new in replace_dict.items():
        input_string = input_string.replace(old, new)
    return input_string


def format_trippel_notation(input_string: str):
    """Replace trippel moves with inverse moves."""
    return input_string.replace("3", "'")


def format_parenteses(input_string: str) -> str:
    """Check parenteses balance and alternate parenteses."""

    # Check if all parentheses are balanced and
    # alternate between normal and inverse parentheses
    stack = []
    output_string = ""
    for char in input_string:
        if char == "(":
            stack.append(char)
            output_string += "(" if len(stack) % 2 else ")"
        elif char == ")":
            if not stack:
                raise ValueError("Unbalanced parentheses!")
            stack.pop()
            output_string += "(" if len(stack) % 2 else ")"
        else:
            output_string += char
    if stack:
        raise ValueError("Unbalanced parentheses!")

    return remove_redundant_parenteses(output_string)


def format_whitespaces(input_string: str):
    """Format whitespaces in a sequence."""

    # Add extra space before starting moves
    input_string = re.sub(r"([RLFBUDMESxyz])", r" \1", input_string)

    # Add space before and after parentheses
    input_string = re.sub(r"(\()", r" \1", input_string)
    input_string = re.sub(r"(\))", r"\1 ", input_string)

    # Remove extra spaces
    input_string = re.sub(r"\s+", " ", input_string)

    # Remove spaces before and after parentheses
    input_string = re.sub(r"\s+\)", ")", input_string)
    input_string = re.sub(r"\(\s+", "(", input_string)

    # Remove spaces before wide moves, apostrophes and double moves
    input_string = re.sub(r"\s+w", "w", input_string)
    input_string = re.sub(r"\s+2", "2", input_string)
    input_string = re.sub(r"\s+'", "'", input_string)

    return input_string.strip()


def format_string(input_string: str) -> list[str]:
    """Format a string for Rubiks Cube. Return a list of moves."""

    # Assume that the input string is valid Rubik's Cube notation
    # Assume that there are no comments in the input string

    # standardize move notation
    input_string = format_wide_notation(input_string)
    input_string = format_trippel_notation(input_string)

    # format parentheses and whitespaces
    input_string = format_parenteses(input_string)
    input_string = format_whitespaces(input_string)

    # split into moves
    moves = []
    niss = False
    for move in input_string.split():
        stripped_move = strip_move(move)
        if move.startswith("("):
            niss = not niss
        moves.append("(" + stripped_move + ")" if niss else stripped_move)
        if move.endswith(")"):
            niss = not niss

    return moves


def is_valid_moves(moves: list[str]) -> bool:
    """Check if a list of moves is valid Rubik's Cube notation."""

    # Check if the sequence has correct moves
    pattern = r"^[RLFBUD][w][2']?$|^[RLUDFBxyzMES][2']?$"

    return all(re.match(pattern, strip_move(move)) for move in moves)


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
    """Niss a move."""
    if move.startswith("("):
        return move.replace("(", "").replace(")", "")
    return "(" + move + ")"


def is_rotation(move: str) -> bool:
    """Return True if the move is a rotation."""
    return move in {" ", "x", "x'", "x2", "y", "y'", "y2", "z", "z'", "z2"}


def apply_rotation(move: str, rotation: str) -> str:
    """Apply a rotation to the move."""
    assert is_rotation(rotation), f"Rotation {rotation} must be a rotation!"

    # rotation of faces
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


if __name__ == "__main__":

    raw_text = "(Fw\t R2 x (U2\nM')L2 Rw2 () F2  ( Bw 2 y' D' F')) // Comment"

    moves, comment = split_into_moves_comment(raw_text)
    print("Moves:", moves)
    print("Comment:", comment)
