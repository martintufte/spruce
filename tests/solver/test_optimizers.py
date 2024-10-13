from rubiks_cube.move.generator import MoveGenerator
from rubiks_cube.solver.actions import get_action_space
from rubiks_cube.solver.optimizers import IndexOptimizer
from rubiks_cube.solver.pattern import get_pattern_state


class TestIndexOptimizer:
    def test_fit_transform(self) -> None:
        step = "solved"
        cube_size = 3
        generator = MoveGenerator("<L, R, U, D, F, B>")

        actions = get_action_space(generator=generator, cube_size=cube_size)
        pattern = get_pattern_state(step=step, cube_size=cube_size)

        optimizer = IndexOptimizer()
        assert optimizer.mask is None

        optimizer.fit_transform(actions=actions, pattern=pattern)
        assert optimizer.mask is not None
