from rubiks_cube.formatting import format_string_to_moves
from rubiks_cube.formatting.string import is_valid_symbols
from rubiks_cube.formatting.string import replace_confusing_chars
from rubiks_cube.formatting.string import strip_comments
from rubiks_cube.move.sequence import MoveSequence


def parse_scramble(raw_scramble: str) -> MoveSequence:
    """Parse a scramble and return the move sequence.

    Args:
        raw_scramble (str): Raw scramble input.

    Returns:
        MoveSequence: List of moves in the scramble.

    Raises:
        ValueError: Invalid symbols entered.

    """
    scramble = strip_comments(raw_scramble)
    scramble = replace_confusing_chars(raw_scramble)

    if not is_valid_symbols(scramble):
        raise ValueError("Invalid symbols entered!")

    moves = format_string_to_moves(scramble)

    return MoveSequence(moves)


def parse_steps(user_input: str) -> list[MoveSequence]:
    """Parse user input lines and return the move list.

    Steps:
    - Strip comments
    - Replace definitions provided by the user
    - Replace substitutions
    - Remove skip characters
    - Check for valid symbols
    - Check for valid moves

    Args:
        user_input (str): User input.

    Returns:
        list[MoveSequence]: List of parsed steps as move sequence.

    Raises:
        ValueError: Invalid rewrite at line <n_lines-i>.
        ValueError: Invalid symbols entered at line <n_lines-i>.
    """
    additional_chars = ""
    ignore_chars = ","
    separator_char = ";"
    definition_symbol = "="
    sub_start = "["
    sub_end = "]"
    arrow = "->"

    def try_substitute(line: str, substitutions: list[str]) -> str:
        """Try to replace a subset with the substitutions."""
        if sub_start in line and sub_end in line:
            start_idx = line.index(sub_start)
            end_idx = line.index(sub_end)
            to_replace = line[start_idx + 1 : end_idx]
            if not format_string_to_moves(to_replace):
                raise ValueError(f"Invalid rewrite at line {n_lines-i}")
            if substitutions:
                line = (
                    line[: line.index(sub_start)]
                    + substitutions.pop()
                    + line[line.index(sub_end) + 1 :]
                )
            else:
                line = line.replace(sub_start, "").replace(sub_end, "")
        return line

    user_lines: list[list[str]] = []
    definitions: dict[str, str] = {}
    substitutions: list[str] = []
    skeletons: list[str] = []
    lines = user_input.strip().split("\n")
    n_lines = len(lines)
    for i, raw_line in enumerate(reversed(lines)):
        full_line = strip_comments(raw_line)
        full_line = replace_confusing_chars(full_line)
        for line_loop in reversed(full_line.split(separator_char)):
            line = line_loop
            if line.strip() == "":
                continue
            for definition, definition_moves in definitions.items():
                line = line.replace(definition, definition_moves)
            for char in ignore_chars:
                line = line.replace(char, "")

            if definition_symbol in line:
                assert (
                    line.count(definition_symbol) == 1
                ), "Only one definition symbol per line allowed!"
                definition, definition_moves = line.split(definition_symbol)
                definition = definition.strip()
                definition_moves = definition_moves.strip()
                assert format_string_to_moves(definition_moves), "Definition moves are invalid!"
                if definition[0] == sub_start and definition[-1] == sub_end:
                    substitutions.append(definition_moves)
                    continue
                else:
                    assert len(definition) == 1, "Definition must be a single character!"
                    assert not is_valid_symbols(
                        definition
                    ), "Definition must not be an inbuild symbol!"
                    assert len(definition_moves) > 0, "Definition must have at least one move!"
                    if not is_valid_symbols(definition_moves, additional_chars):
                        raise ValueError(f"Invalid symbols entered at line {n_lines-i}")
                    definitions[definition] = definition_moves
                    additional_chars += definition
                    continue
            elif line.startswith(arrow):
                assert len(line) > 2, f"Invalid skeleton at line {n_lines-i}"
                assert line.count(arrow) == 1, f"Invalid rewrite at line {n_lines-i}"
                line = line.replace(arrow, "").strip()
                line = try_substitute(line, substitutions)
                if not is_valid_symbols(line, additional_chars):
                    raise ValueError(f"Invalid symbols entered at line {n_lines-i}")
                line_moves = format_string_to_moves(line)
                skeletons.append(line)
                continue
            else:
                line = try_substitute(line, substitutions)

            if not is_valid_symbols(line, additional_chars):
                raise ValueError(f"Invalid symbols entered at line {n_lines-i}")
            line_moves = format_string_to_moves(line)
            user_lines.append(line_moves)

    if skeletons:
        return [MoveSequence(skeletons[0])]

    return [MoveSequence(moves) for moves in reversed(user_lines)]
