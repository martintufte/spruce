import pytest

from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.move.sequence import cleanup
from rubiks_cube.move.sequence import combine_axis_moves
from rubiks_cube.move.sequence import niss
from rubiks_cube.move.sequence import replace_wide_moves
from rubiks_cube.move.sequence import shift_rotations_to_end
from rubiks_cube.move.sequence import slash


@pytest.mark.parametrize(
    "move, expected",
    [
        ("", ""),
        ("x2 y2", "z2"),
        ("y2 z2", "x2"),
        ("z2 x2", "y2"),
        ("x y2 z' x' y2 x2 z' y' x y2 x' z2 y' x2 z' y2", "y"),
    ],
)
def test_move_rotations_to_end(move: str, expected: str) -> None:
    seq = MoveSequence(move)
    shift_rotations_to_end(seq)
    assert seq == MoveSequence(expected)


@pytest.mark.parametrize(
    "move, expected",
    [
        ("", ""),
        ("R R", "R2"),
        ("R L L", "L2 R"),
        ("R2 R2", ""),
        ("R Rw R", "R2 Rw"),
        ("R Rw 3Rw R Rw R", "R' Rw2 3Rw"),
        ("R2 L R2", "L"),
        ("F2 L2 L2 F2", ""),
        ("R R' L R2 U U2 L2 D2 D2 L2  U' B U' B' F B2", "L R2 U2 B U' B F"),
    ],
)
def test_combine_axis_moves(move: str, expected: str) -> None:
    seq = MoveSequence(move)
    combine_axis_moves(seq)
    assert seq == MoveSequence(expected)


@pytest.mark.parametrize(
    "move, expected",
    [
        ("", ""),
        ("Lw", "R x'"),
        ("Rw", "L x"),
        ("Fw", "B z"),
        ("Bw", "F z'"),
        ("Uw", "D y"),
        ("Dw", "U y'"),
    ],
)
def test_replace_wide_moves_3(move: str, expected: str) -> None:
    seq = MoveSequence(move)
    replace_wide_moves(seq, cube_size=3)
    assert seq == MoveSequence(expected)


@pytest.mark.parametrize(
    "move, expected",
    [
        ("", ""),
        ("Lw", "Lw"),
        ("3Rw", "3Rw"),
        ("4Fw", "4Fw"),
        ("5Bw", "4Fw z'"),
        ("6Uw", "3Dw y"),
        ("7Dw", "Uw y'"),
        ("8Lw", "R x'"),
    ],
)
def test_replace_wide_moves_9(move: str, expected: str) -> None:
    seq = MoveSequence(move)
    replace_wide_moves(seq, cube_size=9)
    assert seq == MoveSequence(expected)


@pytest.mark.parametrize(
    "move, expected",
    [
        ("", ""),
        ("3Lw", "x'"),
        ("4Rw", "x"),
        ("5Fw", "z"),
        ("6Bw", "z'"),
        ("7Uw", "y"),
        ("8Dw", "y'"),
    ],
)
def test_replace_wide_moves_outside(move: str, expected: str) -> None:
    seq = MoveSequence(move)
    replace_wide_moves(seq, cube_size=3)
    assert seq == MoveSequence(expected)


def test_cleanup() -> None:
    seq = MoveSequence("(R') L M' (S2) x2 (z)")
    cleaned_seq = cleanup(seq)
    assert cleaned_seq == MoveSequence("L2 R' x' (R' B2 F2 z')")


def test_invert() -> None:
    seq = MoveSequence("L M' x2 (R' S2 z)")
    assert ~seq == MoveSequence("(z' S2 R) x2 M L'")


@pytest.mark.parametrize(
    "move, expected",
    [
        ("R", "(R)"),
        ("(R)", "R"),
        ("~R~", "(~R~)"),
        ("(~R~)", "~R~"),
    ],
)
def test_niss(move: str, expected: str) -> None:
    seq = MoveSequence([move])
    niss(seq)
    assert seq == MoveSequence([expected])


@pytest.mark.parametrize(
    "move, expected",
    [
        ("R", "~R~"),
        ("(R)", "(~R~)"),
        ("~R~", "R"),
        ("(~R~)", "(R)"),
    ],
)
def test_slash(move: str, expected: str) -> None:
    seq = MoveSequence([move])
    slash(seq)
    assert seq == MoveSequence([expected])
