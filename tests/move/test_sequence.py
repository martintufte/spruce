from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.move.sequence import cleanup
from rubiks_cube.move.sequence import combine_axis_moves
from rubiks_cube.move.sequence import replace_wide_moves
from rubiks_cube.move.sequence import shift_rotations_to_end


def test_move_rotations_to_end() -> None:
    rotations = "x y2 z' x' y2 x2 z' y' x y2 x' z2 y' x2 z' y2"  # equals y
    assert shift_rotations_to_end(MoveSequence(rotations)) == MoveSequence("y")


def test_combine_axis_moves() -> None:
    axis_moves = "R R' L R2 U U2 L2 D2 D2 L2  U' B U' B' F B2"
    assert combine_axis_moves(MoveSequence(axis_moves)) == MoveSequence("L R2 U2 B U' B F")


def test_replace_wide_moves() -> None:
    seq = MoveSequence("Rw L Bw2 Fw' D Rw2")
    replace_wide_moves(seq, cube_size=3)
    assert seq == MoveSequence("L x L F2 z2 B' z' D L2 x2")


def test_cleanup() -> None:
    seq = MoveSequence("(R)")
    cleanup(seq)


def test_invert() -> None:
    seq = MoveSequence("R U R' U' (U D)")
    assert ~seq == MoveSequence("(D' U') U R U' R'")


def test_slash() -> None:
    seq = MoveSequence(["~R~"])
    assert ~seq == MoveSequence(["~R'~"])
