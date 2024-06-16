import streamlit as st

from rubiks_cube.utils.formatter import format_string
from rubiks_cube.utils.formatter import is_valid_symbols
from rubiks_cube.utils.formatter import remove_comment
from rubiks_cube.utils.move import is_valid_moves
from rubiks_cube.utils.move import string_to_moves
from rubiks_cube.utils.sequence import MoveSequence
from rubiks_cube.utils.sequence import cleanup


# TODO: Make this return a (Attempt / Workbench) object
def parse_user_input(user_input: str) -> MoveSequence:
    """
    Parse user input lines and return the move list:
    - Remove comments
    - Replace definitions provided by the user
    - Replace substitutions
    - Remove skip characters
    - Check for valid symbols
    - Check for valid moves
    - Combine all moves into a single list of moves
    """
    additional_chars = ""
    skip_chars = ","
    definition_symbol = "="
    sub_start = "["
    sub_end = "]"

    user_lines = []
    definitions = {}
    substitutions = []
    lines = user_input.strip().split("\n")
    n_lines = len(lines)
    for i, line_input in enumerate(reversed(lines)):
        line = remove_comment(line_input)
        if line.strip() == "":
            continue
        for definition, definition_moves in definitions.items():
            line = line.replace(definition, definition_moves)
        for char in skip_chars:
            line = line.replace(char, "")

        if definition_symbol in line:
            definition, definition_moves = line.split(definition_symbol)
            definition = definition.strip()
            definition_moves = definition_moves.strip()
            assert is_valid_moves(string_to_moves(definition_moves)), \
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
                if not is_valid_symbols(definition_moves, additional_chars):
                    st.warning(f"Invalid symbols entered at line {n_lines-i}")
                    break
                definitions[definition] = definition_moves
                additional_chars += definition
                continue
        else:
            if sub_start in line and sub_end in line:
                start_idx = line.index(sub_start)
                end_idx = line.index(sub_end)
                to_replace = line[start_idx+1:end_idx]
                if not is_valid_moves(string_to_moves(to_replace)):
                    st.warning(f"Invalid rewrite at line {n_lines-i}")
                    break
                if substitutions:
                    line = line[:line.index(sub_start)] + \
                        substitutions.pop() + line[line.index(sub_end)+1:]
                else:
                    line = line.replace(sub_start, "").replace(sub_end, "")

        if not is_valid_symbols(line, additional_chars):
            st.warning(f"Invalid symbols entered at line {n_lines-i}")
            break
        line_moves = string_to_moves(format_string(line))
        if not is_valid_moves(line_moves):
            st.warning(f"Invalid moves entered at line {n_lines-i}")
            break
        else:
            user_lines.append(line_moves)

    user_moves = MoveSequence(sum(reversed(user_lines), []))
    return cleanup(user_moves)
