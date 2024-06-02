import re


def is_valid_symbols(input_string: str, additional_chars: str = "") -> bool:
    """
    Check that a string only contains valid symbols.
    Additional symbols can be added to the valid symbols.
    """

    valid_chars = "RLFBUDMESrlfbudxyzw23' ()[]/\t\n" + additional_chars

    return all(char in valid_chars for char in input_string)


def remove_comment(input_string: str) -> str:
    """
    Remove the comment from the input string.
    E.g. "R U R' // Comment" -> "R U R'"
    """

    split_idx = input_string.find("//")
    if split_idx != -1:
        return input_string[:split_idx]

    return input_string


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


def fix_move_rotation(input_string: str) -> str:
    """
    Replace trippel moves with inverse moves and fix apostrophes.
    E.g. R3 -> R', U2' -> U2, F3' -> F, etc.
    """

    output_string = input_string.replace("2'", "2")
    output_string = output_string.replace("3'", "")
    output_string = output_string.replace("3", "'")

    return output_string


def remove_wide_notation(input_string: str) -> str:
    """Replace old wide notation with new wide notation."""

    output_string = input_string
    replace_dict = {
        "u": "Uw", "d": "Dw", "f": "Fw", "b": "Bw", "l": "Lw", "r": "Rw",
    }
    for old, new in replace_dict.items():
        output_string = output_string.replace(old, new)

    return output_string


def format_parenteses(input_string: str) -> str:
    """Check parenteses balance and alternate parenteses."""

    # Use a stack to check for balanced parentheses
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


def format_whitespaces(input_string: str) -> str:
    """Format whitespaces in the input string."""

    # Add space before starting moves
    output_string = re.sub(r"([RLFBUDMESxyz])", r" \1", input_string)
    # Add space around parentheses
    output_string = re.sub(r"(\()", r" \1", output_string)
    output_string = re.sub(r"(\))", r"\1 ", output_string)
    # Remove extra spaces, including tabs and newlines
    output_string = re.sub(r"\s+", " ", output_string)
    # Remove spaces before and after parentheses
    output_string = re.sub(r"\s+\)", ")", output_string)
    output_string = re.sub(r"\(\s+", "(", output_string)
    # Remove spaces before wide moves, apostrophes, double and trippel moves
    output_string = re.sub(r"\s+w", "w", output_string)
    output_string = re.sub(r"\s+2", "2", output_string)
    output_string = re.sub(r"\s+3", "3", output_string)
    output_string = re.sub(r"\s+'", "'", output_string)

    return output_string.strip()


def format_string(input_string: str) -> str:
    """
    Clean up the format of a string of moves for Rubiks Cube.
    It does not change the order of the moves.
    """

    # Raise error on invalid symbols
    if not is_valid_symbols(input_string):
        raise ValueError("Invalid symbols entered!")

    # Format parentheses and whitespaces
    output_string = format_parenteses(input_string)
    output_string = format_whitespaces(output_string)
    output_string = remove_wide_notation(output_string)
    output_string = fix_move_rotation(output_string)

    return output_string


def main() -> None:
    raw_input = "(f\tx R 2 (U2'  M')L\n3D w2() F2 ( Bw 3' y ' F')) // Comment"
    raw_string = remove_comment(raw_input)
    formatted_string = format_string(raw_string)
    print("Raw input:", raw_input)
    print("Formatted string:", formatted_string)


if __name__ == "__main__":
    main()
