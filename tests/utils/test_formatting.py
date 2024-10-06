from rubiks_cube.utils.formatting import format_string
from rubiks_cube.utils.formatting import remove_comment


def test_main() -> None:
    raw_input = "(f\txR 2 (U2'  M')L 3D w2() F2 ( Bw ' y ' F')) // ugly"
    raw_string = remove_comment(raw_input)
    formatted_string = format_string(raw_string)
    print("Raw:", raw_input)
    print("Formatted:", formatted_string)

    raw_input = "Rw3 Fw"
    raw_string = remove_comment(raw_input)
    formatted_string = format_string(raw_string)
    print("Raw:", raw_input)
    print("Formatted:", formatted_string)

    raw_input = "3Uw 3Rw'"
    raw_string = remove_comment(raw_input)
    formatted_string = format_string(raw_string)
    print("Raw:", raw_input)
    print("Formatted:", formatted_string)
