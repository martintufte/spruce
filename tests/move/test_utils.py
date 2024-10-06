from rubiks_cube.move.utils import simplyfy_axis_moves


def test_main() -> None:
    """Test cases for simplyfying axis moves."""

    test_cases: dict[str, str] = {
        "R R'": "",
        "R L R": "L R2",
        "R R R R": "",
        "3Rw' Rw 4Lw2 R L 3Rw2 Lw' R": "L Lw 4Lw R2 Rw 3Rw",
    }

    for i, (case, expected) in enumerate(test_cases.items()):
        print(
            "Scr:",
            case,
            "Exp:",
            expected.split(),
            "Act:",
            simplyfy_axis_moves(case.split()),
        )

    # move widener as int
    """
    test_cases_move_widener: dict[str, int] = {
        "R": 1,
        "L2": 1,
        "F'": 1,
        "Rw": 2,
        "Bw'": 2,
        "Uw2": 2,
        "3Bw'": 3,
        "6Lw2": 6,
    }
    for i, (case, expected) in enumerate(test_cases_move_widener.items()):
        print("Scramble:", case, "Expected:", expected, "Actual:", move_to_coord(case))
    """
