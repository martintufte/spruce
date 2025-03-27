from rubiks_cube.configuration.enumeration import Status
from rubiks_cube.move.generator import MoveGenerator
from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.solver import solve_step


def test_main() -> None:
    """Example of solving a step with a generator on a 3x3 cube."""
    cube_size = 3
    sequence = MoveSequence("x y M2 U M U2 M' U M2")
    generator = MoveGenerator("<M, U>")

    solutions, search_summary = solve_step(
        sequence=sequence,
        generator=generator,
        tag="solved",
        max_search_depth=8,
        n_solutions=1,
        search_inverse=False,
        cube_size=cube_size,
    )
    assert isinstance(solutions, list)
    assert search_summary.walltime > 0
    assert search_summary.n_solutions == 1
    assert search_summary.max_search_depth == 8
    assert search_summary.status == Status.Success
