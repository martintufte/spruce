from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.move.sequence import combine_axis_moves
from rubiks_cube.move.sequence import move_rotations_to_end
from rubiks_cube.move.sequence import replace_wide_moves
from rubiks_cube.utils.formatting import remove_comment


def test_remove_comment() -> None:
    raw_text = "(Fw\t R2 x (U2\nM')L2 Rw' () F2  ( Bw 2 y' D' F')) // Comment"
    moves = remove_comment(raw_text)
    seq = MoveSequence(moves)
    assert seq == MoveSequence("(Fw R2 x) U2 M' (L2 Rw' F2) Bw2 y' D' F'")


def test_move_rotations_to_end() -> None:
    rotations = "x y2 z' x' y2 x2 z' y' x y2 x' z2 y' x2 z' y2"  # equals y
    assert move_rotations_to_end(MoveSequence(rotations)) == MoveSequence("y")


def test_combine_axis_moves() -> None:
    axis_moves = "R R' L R2 U U2 L2 D2 D2 L2  U' B U' B' F B2"
    assert combine_axis_moves(MoveSequence(axis_moves)) == MoveSequence("L R2 U2 B U' B F")


def test_replace_wide_moves() -> None:
    seq = MoveSequence("Rw L Bw2 Fw' D Rw2")
    replace_wide_moves(seq, cube_size=3)
    assert seq == MoveSequence("L x L F2 z2 B' z' D L2 x2")
