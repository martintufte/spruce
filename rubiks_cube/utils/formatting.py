import re


def is_valid_symbols(input_string: str, additional_chars: str = "") -> bool:
    """Check that a string only contains valid symbols.
    Additional symbols can be added to the valid symbols.

    Args:
        input_string (str): Input string.
        additional_chars (str, optional): Additional characters. Defaults to "".

    Returns:
        bool: True if the string only contains valid symbols.
    """

    valid_chars = "LRBFDUlrbfduMSEwxyz23456789'’ ()[]/\t\n" + additional_chars

    return all(char in valid_chars for char in input_string)


def remove_lookalike_chars(input_string: str) -> str:
    """Remove confusing characters from the input string.

    Args:
        input_string (str): Raw input string.

    Returns:
        str: Cleaned input string.

    Examples:
        >>> remove_lookalike_chars("R U R’ // Comment")
        "R U R'"
    """

    replace_dict = {
        "’": "'",
    }
    for old, new in replace_dict.items():
        input_string = input_string.replace(old, new)

    return input_string


def remove_comment(input_string: str) -> str:
    """Remove the comment from the input string.

    Args:
        input_string (str): Input string.

    Returns:
        str: Input string without the comment.

    Examples:
        >>> remove_comment("R U R' // Comment")
        "R U R'"
    """

    split_idx = input_string.find("//")
    if split_idx != -1:
        return input_string[:split_idx]

    return input_string


def remove_redundant_parenteses(input_string: str) -> str:
    """Remove redundant parenteses in a string sequence.

    Args:
        input_string (str): Input string.

    Returns:
        str: Input string without redundant parenteses.

    Examples:
        >>> remove_redundant_parenteses("(R U) (R' U')")
        "(R U R' U')"
        >>> remove_redundant_parenteses("(R U) ()")
        "(R U)"
    """

    output_string = input_string
    while True:
        output_string = re.sub(r"\(\s*\)", "", output_string)
        output_string = re.sub(r"\)\s*\(", "", output_string)
        if output_string == input_string:
            break
        input_string = output_string

    return output_string


def format_move_rotation(input_string: str) -> str:
    """Replace dobbel moves with apostrophes.

    Args:
        input_string (str): Input string.

    Returns:
        str: Input string with apostrophes instead of double moves.

    Examples:
        >>> format_move_rotation("R2'")
        "R2"
    """

    output_string = input_string.replace("2'", "2")

    return output_string


def format_wide_notation(input_string: str) -> str:
    """Format lowrcase wide notation with standard wide notation.

    Args:
        input_string (str): Input string.

    Returns:
        str: Input string with standard wide notation.
    """

    output_string = input_string
    replace_dict = {
        "u": "Uw",
        "d": "Dw",
        "f": "Fw",
        "b": "Bw",
        "l": "Lw",
        "r": "Rw",
    }
    for old, new in replace_dict.items():
        output_string = output_string.replace(old, new)

    return output_string


def format_parenteses(input_string: str) -> str:
    """Format the parenteses in the input string:
    - Use a stack to keep track of the parenteses balance
    - Remove redundant parenteses

    Args:
        input_string (str): Input string.

    Raises:
        ValueError: Unbalanced parentheses!

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

    return remove_redundant_parenteses(output_string)


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


def format_string(valid_string: str) -> str:
    """Clean up the format of a string of valid moves for Rubiks Cube.

    Args:
        valid_string (str): Valid string of moves.

    Returns:
        str: Formatted string of moves.
    """
    output_string = remove_lookalike_chars(valid_string)
    output_string = format_parenteses(output_string)
    output_string = format_whitespaces(output_string)
    output_string = format_wide_notation(output_string)
    output_string = format_move_rotation(output_string)

    return output_string
