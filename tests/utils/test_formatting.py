from rubiks_cube.utils.formatting import format_string
from rubiks_cube.utils.formatting import remove_comment


def test_formatting1() -> None:
    raw_input = "(f\txR 2 (U2'  M')L 3D w2() F2 ( Bw ' y ' F')) // ugly"
    raw_string = remove_comment(raw_input)
    formatted_string = format_string(raw_string)
    assert formatted_string == "(Fw x R2) U2 M' (L 3Dw2 F2) Bw' y' F'"


def test_formatting2() -> None:
    """Test edge case with 2 and 3 in wide moves."""
    raw_input = "Rw3Fw"
    raw_string = remove_comment(raw_input)
    formatted_string = format_string(raw_string)
    assert formatted_string == "Rw 3Fw"

    raw_input = "Rw2Fw"
    raw_string = remove_comment(raw_input)
    formatted_string = format_string(raw_string)
    assert formatted_string == "Rw2 Fw"
