import logging
from typing import Final

from rubiks_cube.configuration.enumeration import State
from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.state.tag.patterns import get_cubexes

LOGGER: Final = logging.getLogger(__name__)


def test_main() -> None:
    cube_size = 3
    cubexes = get_cubexes(cube_size=cube_size)
    sequence = MoveSequence("U")

    LOGGER.info(f'\nMoveSequence "{sequence}" tagged with {len(cubexes)} tags:\n')
    for tag, cbx in sorted(cubexes.items()):
        LOGGER.info(f"{tag} ({len(cbx)}): {cbx.match(sequence, cube_size=cube_size)}")

    LOGGER.info("Missing tags:")
    for state in State:
        if state.value not in cubexes:
            LOGGER.info(f"{state.value}")

    LOGGER.info("\nMatch specific pattern:")
    LOGGER.info(cubexes["f2l-layer"].match(sequence, cube_size=cube_size))
