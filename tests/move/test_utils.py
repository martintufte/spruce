import pytest

from rubiks_cube.move.utils import move_to_coord
from rubiks_cube.move.utils import simplyfy_axis_moves


@pytest.mark.parametrize(
    "case, expected",
    [
        ("R R'", ""),
        ("R L R", "L R2"),
        ("R R R R", ""),
        ("3Rw' Rw 4Lw2 R L 3Rw2 Lw' R", "L Lw' 4Lw2 R2 Rw 3Rw"),
    ],
)
def test_simplify_axis_moves(case: str, expected: str) -> None:
    """Test cases for simplifying axis moves."""
    assert simplyfy_axis_moves(case.split()) == expected.split()


@pytest.mark.parametrize(
    "case, expected",
    [
        ("R", ("R", 1, 1)),
        ("L2", ("L", 1, 2)),
        ("F'", ("F", 1, 3)),
        ("Rw", ("R", 2, 1)),
        ("Bw'", ("B", 2, 3)),
        ("Uw2", ("U", 2, 2)),
        ("3Bw'", ("B", 3, 3)),
        ("6Lw2", ("L", 6, 2)),
    ],
)
def test_move_to_coord(case: str, expected: tuple[str, int, int]) -> None:
    assert move_to_coord(case) == expected
