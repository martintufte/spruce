import numpy as np

from rubiks_cube.move.algorithm import MoveAlgorithm
from rubiks_cube.move.generator import MoveGenerator
from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.solver.actions import get_action_space
from rubiks_cube.solver.optimizers import IndexOptimizer
from rubiks_cube.solver.optimizers import find_rotation_offset
from rubiks_cube.state import get_rubiks_cube_state
from rubiks_cube.tag import get_rubiks_cube_pattern


def test_find_rotation_offset() -> None:
    sequence = MoveSequence("x y z")
    cube_size = 3
    permutation = get_rubiks_cube_state(sequence=sequence, cube_size=cube_size)
    mask = np.zeros_like(permutation, dtype=bool)

    offset = find_rotation_offset(permutation=permutation, mask=mask)
    assert np.all(offset == permutation)


class TestIndexOptimizer:
    def test_standard(self) -> None:
        tag = "solved"
        cube_size = 3
        generator = MoveGenerator("<L, R, U, D, F, B>")

        actions = get_action_space(generator=generator, cube_size=cube_size)
        pattern = get_rubiks_cube_pattern(tag=tag, cube_size=cube_size)

        optimizer = IndexOptimizer(cube_size=cube_size)

        optimizer.fit_transform(actions=actions, pattern=pattern)
        assert sum(optimizer.affected_mask) == 48
        assert sum(optimizer.isomorphic_mask) == 48

    def test_2gen(self) -> None:
        tag = "solved"
        cube_size = 3
        generator = MoveGenerator("<R, U>")

        actions = get_action_space(generator=generator, cube_size=cube_size)
        pattern = get_rubiks_cube_pattern(tag=tag, cube_size=cube_size)

        optimizer = IndexOptimizer(cube_size=cube_size)

        optimizer.fit_transform(actions=actions, pattern=pattern)
        assert sum(optimizer.affected_mask) == 32
        assert sum(optimizer.isomorphic_mask) == 25

    def test_3gen_adjasent(self) -> None:
        tag = "solved"
        cube_size = 3
        generator = MoveGenerator("<R, U, F>")

        actions = get_action_space(generator=generator, cube_size=cube_size)
        pattern = get_rubiks_cube_pattern(tag=tag, cube_size=cube_size)

        optimizer = IndexOptimizer(cube_size=cube_size)

        optimizer.fit_transform(actions=actions, pattern=pattern)
        assert sum(optimizer.affected_mask) == 39
        assert sum(optimizer.isomorphic_mask) == 39

    def test_3gen_opposite(self) -> None:
        tag = "solved"
        cube_size = 3
        generator = MoveGenerator("<R, U, D>")

        actions = get_action_space(generator=generator, cube_size=cube_size)
        pattern = get_rubiks_cube_pattern(tag=tag, cube_size=cube_size)

        optimizer = IndexOptimizer(cube_size=cube_size)

        optimizer.fit_transform(actions=actions, pattern=pattern)
        assert sum(optimizer.affected_mask) == 44
        assert sum(optimizer.isomorphic_mask) == 34

    def test_dr(self) -> None:
        tag = "solved"
        cube_size = 3
        generator = MoveGenerator("<L2, R2, U, D, F2, B2>")

        actions = get_action_space(generator=generator, cube_size=cube_size)
        pattern = get_rubiks_cube_pattern(tag=tag, cube_size=cube_size)

        optimizer = IndexOptimizer(cube_size=cube_size)

        optimizer.fit_transform(actions=actions, pattern=pattern)
        assert sum(optimizer.affected_mask) == 48
        assert sum(optimizer.isomorphic_mask) == 20

    def test_htr(self) -> None:
        tag = "solved"
        cube_size = 3
        generator = MoveGenerator("<L2, R2, U2, D2, F2, B2>")

        actions = get_action_space(generator=generator, cube_size=cube_size)
        pattern = get_rubiks_cube_pattern(tag=tag, cube_size=cube_size)

        optimizer = IndexOptimizer(cube_size=cube_size)

        optimizer.fit_transform(actions=actions, pattern=pattern)
        assert sum(optimizer.affected_mask) == 48
        assert sum(optimizer.isomorphic_mask) == 20

    def test_roux(self) -> None:
        tag = "solved"
        cube_size = 3
        generator = MoveGenerator("<M, U>")

        actions = get_action_space(generator=generator, cube_size=cube_size)
        pattern = get_rubiks_cube_pattern(tag=tag, cube_size=cube_size)

        optimizer = IndexOptimizer(cube_size=cube_size)

        optimizer.fit_transform(actions=actions, pattern=pattern)
        assert sum(optimizer.affected_mask) == 28
        assert sum(optimizer.isomorphic_mask) == 20

    def test_tperm(self) -> None:
        tag = "solved"
        tperm = MoveAlgorithm("T-perm", "R U R' U' R' F R2 U' R' U' R U R' F'")
        cube_size = 3

        actions = get_action_space(algorithms=[tperm], cube_size=cube_size)
        pattern = get_rubiks_cube_pattern(tag=tag, cube_size=cube_size)

        optimizer = IndexOptimizer(cube_size=cube_size)
        actions, pattern = optimizer.fit_transform(actions=actions, pattern=pattern)

        assert sum(optimizer.affected_mask) == 10
        assert sum(optimizer.isomorphic_mask) == 2

    def test_uperm(self) -> None:
        tag = "solved"
        uperm = MoveAlgorithm("Ua-perm", "M2 U M U2 M' U M2")
        cube_size = 3

        actions = get_action_space(algorithms=[uperm], cube_size=cube_size)
        pattern = get_rubiks_cube_pattern(tag=tag, cube_size=cube_size)

        optimizer = IndexOptimizer(cube_size=cube_size)
        actions, pattern = optimizer.fit_transform(actions=actions, pattern=pattern)

        assert sum(optimizer.affected_mask) == 6
        assert sum(optimizer.isomorphic_mask) == 3
