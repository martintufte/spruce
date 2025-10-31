import numpy as np

from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.representation import get_rubiks_cube_state
from rubiks_cube.solver.rotation import find_rotation_offset


def test_find_rotation_offset() -> None:
    sequence = MoveSequence("x y z")
    cube_size = 3
    permutation = get_rubiks_cube_state(sequence=sequence, cube_size=cube_size)
    mask = np.zeros_like(permutation, dtype=bool)

    offset = find_rotation_offset(permutation=permutation, affected_mask=mask, cube_size=cube_size)
    assert np.all(offset == permutation)
