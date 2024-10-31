import logging
from typing import Final

from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.state import get_rubiks_cube_state
from rubiks_cube.tag.cubex import get_cubexes

LOGGER: Final = logging.getLogger(__name__)


def test_main() -> None:
    cube_size = 3
    cubexes = get_cubexes(cube_size=cube_size)
    sequence = MoveSequence("F2")

    LOGGER.info(f'\nMoveSequence "{sequence}" tagged with {len(cubexes)} tags:\n')
    for tag, cbx in cubexes.items():
        permutation = get_rubiks_cube_state(sequence, cube_size=cube_size)
        LOGGER.info(f"{tag} ({len(cbx)}): {cbx.match(permutation, cube_size=cube_size)}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_main()
