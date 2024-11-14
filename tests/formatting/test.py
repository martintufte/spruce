from rubiks_cube.formatting import format_string_to_moves


def test_format_string_to_moves() -> None:
    string = "(fx R2) ()U2M(\t)' (L' Dw2 F2) b y'F'"
    moves = format_string_to_moves(string)
    assert moves == ["(Fw)", "(x)", "(R2)", "U2", "M'", "(L')", "(Dw2)", "(F2)", "Bw", "y'", "F'"]
