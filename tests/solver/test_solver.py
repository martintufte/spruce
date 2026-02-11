from __future__ import annotations

from rubiks_cube.configuration import DEFAULT_GENERATOR
from rubiks_cube.configuration.enumeration import Goal
from rubiks_cube.configuration.enumeration import Status
from rubiks_cube.move.generator import MoveGenerator
from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.solver import solve_pattern


def test_main() -> None:
    """Example of solving a step with a generator on a 3x3 cube."""
    cube_size = 3
    sequence = MoveSequence.from_str("M2 U M U2 M' U M2")
    generator = MoveGenerator.from_str("<M, U>")

    search_summary = solve_pattern(
        sequence=sequence,
        generator=generator,
        goal=Goal.solved,
        max_search_depth=8,
        max_solutions=1,
        search_inverse=False,
        cube_size=cube_size,
    )
    solutions = search_summary.solutions

    assert isinstance(solutions, list)
    assert len(solutions) == 1
    assert search_summary.walltime > 0
    assert search_summary.status is Status.Success


def test_default() -> None:
    """Example of solving a step with a generator on a 3x3 cube."""
    cube_size = 3
    scrambles = [
        MoveSequence.from_str("L"),
        MoveSequence.from_str("R"),
        MoveSequence.from_str("U"),
        MoveSequence.from_str("D"),
        MoveSequence.from_str("F"),
        MoveSequence.from_str("B"),
    ]
    generator = MoveGenerator.from_str(DEFAULT_GENERATOR)

    for scramble in scrambles:
        search_summary = solve_pattern(
            sequence=scramble,
            generator=generator,
            goal=Goal.solved,
            max_search_depth=10,
            max_solutions=2,
            search_inverse=False,
            cube_size=cube_size,
        )
        solutions = search_summary.solutions
        assert len(solutions) == 2
        assert isinstance(solutions, list)
        assert search_summary.walltime > 0
        assert search_summary.status is Status.Success

        # First solution has length == 1
        assert len(solutions[0]) == 1
        # Second solution has length == 8
        assert len(solutions[1]) == 8


if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.WARNING)
    LOGGER = logging.getLogger(__name__)

    test_default()
