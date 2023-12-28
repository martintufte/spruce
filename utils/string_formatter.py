import re


def is_valid_symbols(input_string: str, additional_chars: str = "") -> bool:
    """Check that a string only contains valid symbols."""
    valid_chars = "RLFBUDMESrlfbudxyzw23' ()/\t\n" + additional_chars
    return all(char in valid_chars for char in input_string)


def split_into_moves_comment(input_string: str) -> tuple[str, str]:
    """Split an input string into moves and comment."""
    split_idx = input_string.find("//")
    if split_idx > 0:
        return input_string[:split_idx], input_string[(split_idx+2):]
    return input_string, ""


def remove_redundant_parenteses(input_string: str) -> str:
    """Remove redundant moves in a sequence."""
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
    output_string = input_string
    replace_dict = {
        "u": "Uw", "d": "Dw", "f": "Fw", "b": "Bw", "l": "Lw", "r": "Rw",
    }
    for old, new in replace_dict.items():
        output_string = output_string.replace(old, new)
    return output_string


def format_trippel_notation(input_string: str):
    """Replace trippel moves with inverse moves."""
    output_string = input_string.replace("3", "'")
    output_string = output_string.replace("''", "")
    return output_string


def format_parenteses(input_string: str) -> str:
    """Check parenteses balance and alternate parenteses."""
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
    output_string = re.sub(r"([RLFBUDMESxyz])", r" \1", input_string)
    # Add space before and after parentheses
    output_string = re.sub(r"(\()", r" \1", output_string)
    output_string = re.sub(r"(\))", r"\1 ", output_string)
    # Remove extra spaces
    output_string = re.sub(r"\s+", " ", output_string)
    # Remove spaces before and after parentheses
    output_string = re.sub(r"\s+\)", ")", output_string)
    output_string = re.sub(r"\(\s+", "(", output_string)
    # Remove spaces before wide moves, apostrophes and double moves
    output_string = re.sub(r"\s+w", "w", output_string)
    output_string = re.sub(r"\s+2", "2", output_string)
    output_string = re.sub(r"\s+'", "'", output_string)
    return output_string.strip()


def format_string(input_string: str) -> str:
    """Format a string for Rubiks Cube. Return a list of moves."""
    # Remove invalid symbols
    if not is_valid_symbols(input_string):
        raise ValueError("Invalid symbols entered!")
    # Format wide notation, trippel notatio, parentheses and whitespaces
    output_string = format_wide_notation(input_string)
    output_string = format_trippel_notation(output_string)
    output_string = format_parenteses(output_string)
    output_string = format_whitespaces(output_string)
    return output_string


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
    raw_input = "(Fw\t R2 x (U2  M')L2 R w2 () F2 ( Bw 3' y' D' F')) // Comm"
    raw_string, raw_comment = split_into_moves_comment(raw_input)
    formatted_string = format_string(raw_string)
    print("Formatted string:", formatted_string)
