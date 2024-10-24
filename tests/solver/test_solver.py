from rubiks_cube.move.generator import MoveGenerator
from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.solver import solve_step


def test_main() -> None:
    """Example of solving a step with a generator on a 3x3 cube."""
    cube_size = 3
    sequence = MoveSequence("xy U' R U R2 U' R U R2")
    generator = MoveGenerator("<U, R>")
    step = "solved"
    max_search_depth = 8
    n_solutions = 1
    search_inverse = False

    solutions = solve_step(
        sequence=sequence,
        generator=generator,
        step=step,
        max_search_depth=max_search_depth,
        n_solutions=n_solutions,
        search_inverse=search_inverse,
        cube_size=cube_size,
    )
    assert isinstance(solutions, list)
    assert len(solutions) == 1
