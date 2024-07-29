from rubiks_cube.utils.formatter import is_valid_symbols
from rubiks_cube.utils.formatter import remove_comment
from rubiks_cube.move import format_string_to_moves
from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.move.sequence import cleanup


def parse_scramble(scramble_input: str) -> MoveSequence:
    """Parse a scramble and return the move list.

    Args:
        scramble_input (str): Raw scramble input.

    Raises:
        ValueError: Invalid symbols entered.

    Returns:
        MoveSequence: List of moves in the scramble.
    """
    scramble = remove_comment(scramble_input)
    if not is_valid_symbols(scramble):
        raise ValueError("Invalid symbols entered!")
    scramble_moves = format_string_to_moves(scramble)

    return MoveSequence(scramble_moves)


def parse_user_input(user_input: str) -> MoveSequence:
    """Parse user input lines and return the move list:
    - Remove comments
    - Replace definitions provided by the user
    - Replace substitutions
    - Remove skip characters
    - Check for valid symbols
    - Check for valid moves
    - Combine all moves into a single list of moves
    """
    additional_chars = ""
    ignore_chars = ","
    separator_char = ";"
    definition_symbol = "="
    sub_start = "["
    sub_end = "]"
    arrow = "->"

    def try_substitute(line: str, substitutions: list[str]) -> str:
        """ Try to replace a subset with the substitutions."""
        if sub_start in line and sub_end in line:
            start_idx = line.index(sub_start)
            end_idx = line.index(sub_end)
            to_replace = line[start_idx+1:end_idx]
            if not format_string_to_moves(to_replace):
                raise ValueError(
                    f"Invalid rewrite at line {n_lines-i}"
                )
            if substitutions:
                line = line[:line.index(sub_start)] + \
                    substitutions.pop() + line[line.index(sub_end)+1:]
            else:
                line = line.replace(sub_start, "").replace(sub_end, "")
        return line

    user_lines = []
    definitions = {}
    substitutions = []
    skeletons = []
    lines = user_input.strip().split("\n")
    n_lines = len(lines)
    for i, line_input in enumerate(reversed(lines)):
        full_line = remove_comment(line_input)
        for line in reversed(full_line.split(separator_char)):
            if line.strip() == "":
                continue
            for definition, definition_moves in definitions.items():
                line = line.replace(definition, definition_moves)
            for char in ignore_chars:
                line = line.replace(char, "")

            if definition_symbol in line:
                assert line.count(definition_symbol) == 1, \
                    "Only one definition symbol per line allowed!"
                definition, definition_moves = line.split(definition_symbol)
                definition = definition.strip()
                definition_moves = definition_moves.strip()
                assert format_string_to_moves(definition_moves), \
                    "Definition moves are invalid!"
                if definition[0] == sub_start and definition[-1] == sub_end:
                    substitutions.append(definition_moves)
                    continue
                else:
                    assert len(definition) == 1, \
                        "Definition must be a single character!"
                    assert not is_valid_symbols(definition), \
                        "Definition must not be an inbuild symbol!"
                    assert len(definition_moves) > 0, \
                        "Definition must have at least one move!"
                    if not is_valid_symbols(definition_moves, additional_chars):  # noqa: E501
                        raise ValueError(
                            f"Invalid symbols entered at line {n_lines-i}"
                        )
                    definitions[definition] = definition_moves
                    additional_chars += definition
                    continue
            elif line.startswith(arrow):
                assert len(line) > 2, f"Invalid skeleton at line {n_lines-i}"  # noqa: E501
                assert line.count(arrow) == 1, f"Invalid rewrite at line {n_lines-i}"  # noqa: E501
                line = line.replace(arrow, "").strip()
                line = try_substitute(line, substitutions)
                if not is_valid_symbols(line, additional_chars):
                    raise ValueError(f"Invalid symbols entered at line {n_lines-i}")  # noqa: E501
                line_moves = format_string_to_moves(line)
                skeletons.append(line)
                continue
            else:
                line = try_substitute(line, substitutions)

            if not is_valid_symbols(line, additional_chars):
                raise ValueError(f"Invalid symbols entered at line {n_lines-i}")  # noqa: E501
            line_moves = format_string_to_moves(line)
            user_lines.append(line_moves)

    if skeletons:
        user_moves = MoveSequence(skeletons[0])
    else:
        user_moves = MoveSequence(sum(reversed(user_lines), []))
    return cleanup(user_moves)


def parse_attempt(attempt_input: str) -> list[MoveSequence]:
    """Parse user input lines and return the move list:
    - Remove comments
    - Replace definitions provided by the user
    - Replace substitutions
    - Remove skip characters
    - Check for valid symbols
    - Check for valid moves
    - Combine all moves into a single list of moves
    """
    additional_chars = ""
    ignore_chars = ","
    separator_char = ";"
    definition_symbol = "="
    sub_start = "["
    sub_end = "]"
    arrow = "->"

    def try_substitute(line: str, substitutions: list[str]) -> str:
        """ Try to replace a subset with the substitutions."""
        if sub_start in line and sub_end in line:
            start_idx = line.index(sub_start)
            end_idx = line.index(sub_end)
            to_replace = line[start_idx+1:end_idx]
            if not format_string_to_moves(to_replace):
                raise ValueError(
                    f"Invalid rewrite at line {n_lines-i}"
                )
            if substitutions:
                line = line[:line.index(sub_start)] + \
                    substitutions.pop() + line[line.index(sub_end)+1:]
            else:
                line = line.replace(sub_start, "").replace(sub_end, "")
        return line

    user_lines = []
    definitions = {}
    substitutions = []
    skeletons = []
    lines = attempt_input.strip().split("\n")
    n_lines = len(lines)
    for i, line_input in enumerate(reversed(lines)):
        full_line = remove_comment(line_input)
        for line in reversed(full_line.split(separator_char)):
            if line.strip() == "":
                continue
            for definition, definition_moves in definitions.items():
                line = line.replace(definition, definition_moves)
            for char in ignore_chars:
                line = line.replace(char, "")

            if definition_symbol in line:
                assert line.count(definition_symbol) == 1, \
                    "Only one definition symbol per line allowed!"
                definition, definition_moves = line.split(definition_symbol)
                definition = definition.strip()
                definition_moves = definition_moves.strip()
                assert format_string_to_moves(definition_moves), \
                    "Definition moves are invalid!"
                if definition[0] == sub_start and definition[-1] == sub_end:
                    substitutions.append(definition_moves)
                    continue
                else:
                    assert len(definition) == 1, \
                        "Definition must be a single character!"
                    assert not is_valid_symbols(definition), \
                        "Definition must not be an inbuild symbol!"
                    assert len(definition_moves) > 0, \
                        "Definition must have at least one move!"
                    if not is_valid_symbols(definition_moves, additional_chars):  # noqa: E501
                        raise ValueError(
                            f"Invalid symbols entered at line {n_lines-i}"
                        )
                    definitions[definition] = definition_moves
                    additional_chars += definition
                    continue
            elif line.startswith(arrow):
                assert len(line) > 2, f"Invalid skeleton at line {n_lines-i}"  # noqa: E501
                assert line.count(arrow) == 1, f"Invalid rewrite at line {n_lines-i}"  # noqa: E501
                line = line.replace(arrow, "").strip()
                line = try_substitute(line, substitutions)
                if not is_valid_symbols(line, additional_chars):
                    raise ValueError(f"Invalid symbols entered at line {n_lines-i}")  # noqa: E501
                line_moves = format_string_to_moves(line)
                skeletons.append(line)
                continue
            else:
                line = try_substitute(line, substitutions)

            if not is_valid_symbols(line, additional_chars):
                raise ValueError(f"Invalid symbols entered at line {n_lines-i}")  # noqa: E501
            line_moves = format_string_to_moves(line)
            user_lines.append(line_moves)

    if skeletons:
        return [MoveSequence(skeletons[0])]

    return [MoveSequence(moves) for moves in reversed(user_lines)]
