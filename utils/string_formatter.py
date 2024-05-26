import re


def split_into_moves_comment(input_string: str) -> tuple[str, str]:
    """Split an input string into moves and comment."""

    split_idx = input_string.find("//")
    if split_idx > 0:
        return input_string[:split_idx], input_string[(split_idx+2):]

    return input_string, ""


def is_valid_symbols(input_string: str, additional_chars: str = "") -> bool:
    """Check that a string only contains valid symbols."""

    valid_chars = "RLFBUDMESrlfbudxyzw23' ()[]/\t\n" + additional_chars

    return all(char in valid_chars for char in input_string)


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


def main() -> None:
    raw_input = "(Fw\t R2 x (U2  M')L2 R w2 () F2 ( Bw 3' y' D' F')) // Comm"

    print("Raw input:", raw_input)

    raw_string, raw_comment = split_into_moves_comment(raw_input)
    formatted_string = format_string(raw_string)

    print("Formatted string:", formatted_string)


if __name__ == "__main__":
    main()
