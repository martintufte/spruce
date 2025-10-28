import logging
from typing import Final

from rubiks_cube.configuration.logging import configure_logging
from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.representation import get_rubiks_cube_state
from rubiks_cube.tag.cubex import get_cubexes

LOGGER: Final = logging.getLogger(__name__)


class TestCubexContains:
    def test_dr_contains_eo(self) -> None:
        cube_size = 3
        cubexes = get_cubexes(cube_size=cube_size)

        assert cubexes["eo-fb"] in cubexes["dr-ud"]
        assert cubexes["dr-ud"] not in cubexes["eo-fb"]

    def test_solved_contains_all(self) -> None:
        cube_size = 3
        cubexes = get_cubexes(cube_size=cube_size)

        for pattern in cubexes:
            assert cubexes[pattern] in cubexes["solved"]
            if pattern != "solved":
                assert cubexes["solved"] not in cubexes[pattern]


def test_main() -> None:
    cube_size = 3
    cubexes = get_cubexes(cube_size=cube_size)
    sequence = MoveSequence("F2")
    permutation = get_rubiks_cube_state(sequence, cube_size=cube_size)
    sum_subsets = sum(len(cbx) for cbx in cubexes.values())

    LOGGER.info(f'\nMoveSequence "{sequence}" tagged with {len(cubexes)} tags ({sum_subsets}):\n')
    for pattern, cbx in cubexes.items():
        LOGGER.info(f"[{round(cbx.entropy, 2)}] {pattern} ({len(cbx)}): {cbx.match(permutation)}")


if __name__ == "__main__":
    configure_logging()
    test_main()
