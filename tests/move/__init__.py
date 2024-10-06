from rubiks_cube.move import format_string_to_moves


def test_main() -> None:
    string = "(fx R2) ()U2M(\t)' (L' Dw2 F2) b y'F'"
    moves = format_string_to_moves(string)
    print("Raw:", string)
    print("Formatted:", " ".join(moves).replace(") (", " "))
