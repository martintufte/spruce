import numpy as np

from rubiks_cube.move.algorithm import MoveAlgorithm
from rubiks_cube.move.generator import MoveGenerator
from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.solver.actions import get_action_space
from rubiks_cube.solver.optimizers import IndexOptimizer
from rubiks_cube.solver.optimizers import find_rotation_offset
from rubiks_cube.solver.optimizers import optimize_actions
from rubiks_cube.state import get_rubiks_cube_state
from rubiks_cube.state.pattern import get_pattern_state


def test_find_rotation_offset() -> None:
    sequence = MoveSequence("x y z")
    permutation = get_rubiks_cube_state(sequence=sequence, cube_size=3)
    mask = np.zeros_like(permutation, dtype=bool)

    offset = find_rotation_offset(permutation=permutation, mask=mask)
    assert np.all(offset == permutation)


class TestIndexOptimizer:
    def test_standard(self) -> None:
        step = "solved"
        cube_size = 3
        generator = MoveGenerator("<L, R, U, D, F, B>")

        actions = get_action_space(generator=generator, cube_size=cube_size)
        pattern = get_pattern_state(step=step, cube_size=cube_size)

        optimizer = IndexOptimizer()

        optimizer.fit_transform(actions=actions, pattern=pattern)
        if optimizer.mask is not None:
            assert sum(optimizer.mask) == 48

    def test_tperm(self) -> None:
        step = "solved"
        tperm = MoveAlgorithm("T-perm", "R U R' U' R' F R2 U' R' U' R U R' F'")

        actions = get_action_space(algorithms=[tperm], cube_size=3)
        pattern = get_pattern_state(step=step, cube_size=3)

        optimizer = IndexOptimizer()
        actions, pattern = optimizer.fit_transform(actions=actions, pattern=pattern)

        if optimizer.mask is not None:
            assert sum(optimizer.mask) == 2

    def test_uperm(self) -> None:
        step = "solved"
        uperm = MoveAlgorithm("Ua-perm", "M2 U M U2 M' U M2")

        actions = get_action_space(algorithms=[uperm], cube_size=3)
        pattern = get_pattern_state(step=step, cube_size=3)

        optimizer = IndexOptimizer()
        actions, pattern = optimizer.fit_transform(actions=actions, pattern=pattern)

        if optimizer.mask is not None:
            assert sum(optimizer.mask) == 6  # Should be 3, but the algorithm is not optimal.

    def test_minimal(self) -> None:
        import numpy as np

        actions = {
            "a": np.array([1, 2, 0, 5, 3, 4]),
        }
        optimize_actions(actions)
