from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.move.sequence import cleanup
from rubiks_cube.move.sequence import combine_axis_moves
from rubiks_cube.move.sequence import move_rotations_to_end
from rubiks_cube.move.sequence import replace_wide_moves
from rubiks_cube.utils.formatting import remove_comment


def test_main() -> None:
    raw_text = "(Fw\t R2 x (U2\nM')L2 Rw' () F2  ( Bw 2 y' D' F')) // Comment"
    moves = remove_comment(raw_text)
    seq = MoveSequence(moves)
    print("\nMoves:", seq)
    print("Cleaned:", cleanup(seq))

    rotations = "x y2 z' x' y2 x2 z' y' x y2 x' z2 y' x2 z' y2"  # equals y
    print("\nRotations:", MoveSequence(rotations))
    print("Reduced:", move_rotations_to_end(MoveSequence(rotations)))

    axis_moves = "R R' L R2 U U2 L2 D2 D2 L2  U' B U' B' F B2"
    print("\nAxis moves:", MoveSequence(axis_moves))
    print("Combined:", combine_axis_moves(MoveSequence(axis_moves)))

    seq = MoveSequence("Rw L Bw2 Fw' D Rw2")
    print(seq)
    replace_wide_moves(seq)
    print(seq)
