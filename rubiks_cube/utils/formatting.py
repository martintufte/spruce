import re


def strip_comments(input_string: str) -> str:
    """Strip the comments from the input string.

    Args:
        input_string (str): Input string.

    Returns:
        str: Input string without the comment.
    """

    split_idx = input_string.find("//")
    output_string = input_string[:split_idx] if split_idx != -1 else input_string

    return output_string.rstrip()


def replace_confusing_chars(input_string: str) -> str:
    """Replace confusing characters from the input string.

    Args:
        input_string (str): Raw input string.

    Returns:
        str: Input string without confusing characters.
    """

    output_string = input_string.replace("’", "'")
    output_string = output_string.replace("‘", "'")
    output_string = output_string.replace("ʼ", "'")

    return output_string


def is_valid_symbols(input_string: str, additional_chars: str = "") -> bool:
    """Check that a string only contains valid symbols.
    Additional symbols can be added to the valid symbols.

    Args:
        input_string (str): Input string.
        additional_chars (str, optional): Additional characters. Defaults to "".

    Returns:
        bool: True if the string only contains valid symbols.
    """

    valid_chars = "LRBFDUlrbfduMSEwxyz23456789' ()\t\n" + additional_chars

    return all(char in valid_chars for char in input_string)


def format_parenteses(input_string: str) -> str:
    """Format the parenteses in the input string:
    - Try balance the parenteses.
    - Remove redundant parenteses.

    Args:
        input_string (str): Input string.

    Raises:
        ValueError: Unbalanced parentheses!

    Returns:
        str: Input string with balanced parenteses.
    """

    output_string = try_balance_parenteses(input_string)
    output_string = remove_redundant_parenteses(output_string)

    return output_string


def try_balance_parenteses(input_string: str) -> str:
    """Balance the parenteses in the input string.

    Args:
        input_string (str): Input string.

    Raises:
        ValueError: Unbalanced parentheses.

    Returns:
        str: Input string with balanced parenteses.
    """

    stack: list[str] = []
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

    return output_string


def remove_redundant_parenteses(input_string: str) -> str:
    """Remove redundant parenteses in a string sequence.

    Args:
        input_string (str): Input string.

    Returns:
        str: Input string without redundant parenteses.
    """

    output_string = input_string
    while True:
        output_string = re.sub(r"\(\s*\)", "", output_string)
        output_string = re.sub(r"\)\s*\(", " ", output_string)
        if output_string == input_string:
            break
        input_string = output_string

    return output_string


def format_whitespaces(input_string: str) -> str:
    """Format whitespaces in the input string:

    - Add spaces before starting moves
    - Set the widener int next to the moves
    - Add spaces around parentheses
    - Remove extra white space, including tabs and newlines
    - Remove spaces before and after parentheses
    - Remove spaces before wide moves, apostrophes, double moves

    Args:
        input_string (str): Input string.

    Returns:
        str: Input string with formatted whitespaces.
    """

    output_string = re.sub(r"([rlfbudRLFBUDMESxyz])", r" \1", input_string)

    output_string = re.sub(r"([3456789])\s+", r" \1", output_string)

    output_string = re.sub(r"(\()", r" \1", output_string)
    output_string = re.sub(r"(\))", r"\1 ", output_string)

    output_string = re.sub(r"\s+", " ", output_string)

    output_string = re.sub(r"\s+\)", ")", output_string)
    output_string = re.sub(r"\(\s+", "(", output_string)

    output_string = re.sub(r"\s+w", "w", output_string)
    output_string = re.sub(r"\s+2", "2", output_string)
    output_string = re.sub(r"\s+'", "'", output_string)

    return output_string.strip()


def format_notation(input_string: str) -> str:
    """Format the notation of the input string:

    - Replace lowercase wide notation with standard wide notation
    - Replace double moves with apostrophes

    Args:
        input_string (str): Input string.

    Returns:
        str: Input string with standard notation.
    """

    output_string = replace_wide_notation(input_string)
    output_string = replace_move_rotation(output_string)

    return output_string


def replace_move_rotation(input_string: str) -> str:
    """Replace dobbel moves with apostrophes.

    Args:
        input_string (str): Input string.

    Returns:
        str: Input string with apostrophes instead of double moves.
    """

    return input_string.replace("2'", "2")


def replace_wide_notation(input_string: str) -> str:
    """Format lowrcase wide notation with standard wide notation.

    Args:
        input_string (str): Input string.

    Returns:
        str: Input string with standard wide notation.
    """

    output_string = input_string.replace("u", "Uw")
    output_string = output_string.replace("d", "Dw")
    output_string = output_string.replace("f", "Fw")
    output_string = output_string.replace("b", "Bw")
    output_string = output_string.replace("l", "Lw")
    output_string = output_string.replace("r", "Rw")

    return output_string


def format_string(valid_string: str) -> str:
    """Clean up the format of a string of valid moves for Rubiks Cube.

    Args:
        valid_string (str): Valid string of moves.

    Returns:
        str: Formatted string of moves.
    """
    output_string = format_parenteses(valid_string)
    output_string = format_whitespaces(output_string)
    output_string = format_notation(output_string)

    return output_string
