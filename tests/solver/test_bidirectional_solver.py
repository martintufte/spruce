from rubiks_cube.move.generator import MoveGenerator
from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.solver.bidirectional_solver import solve_step


def test_main() -> None:
    """Example of solving a step with a generator on a 3x3 cube."""
    cube_size = 10
    sequence = MoveSequence("4Uw 4Fw 4Lw 4Dw")
    generator = MoveGenerator("<4Lw, 4Rw, 4Fw, 4Bw, 4Uw, 4Dw>")
    step = "solved"
    max_search_depth = 8
    n_solutions = 1
    search_inverse = False

    print("Sequence:", sequence)
    print("Generator:", generator, "\tStep:", step)

    solutions = solve_step(
        sequence=sequence,
        generator=generator,
        step=step,
        max_search_depth=max_search_depth,
        n_solutions=n_solutions,
        search_inverse=search_inverse,
        cube_size=cube_size,
    )

    print("Solutions:")
    for solution in solutions if solutions is not None else []:
        print(solution)
