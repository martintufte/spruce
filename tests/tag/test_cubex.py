import logging
from typing import Final

from rubiks_cube.configuration.enumeration import Piece
from rubiks_cube.move.generator import MoveGenerator
from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.state import get_rubiks_cube_state
from rubiks_cube.tag.simple_cubex import CubexCollection
from rubiks_cube.tag.simple_cubex import get_cubexes

LOGGER: Final = logging.getLogger(__name__)


def test_main_simple() -> None:
    cube_size = 3
    cubexes = get_cubexes(cube_size=cube_size)
    sequence = MoveSequence("F2")

    LOGGER.info(f'\nMoveSequence "{sequence}" tagged with {len(cubexes)} tags:\n')
    for tag, cbx in cubexes.items():
        permutation = get_rubiks_cube_state(sequence, cube_size=cube_size)
        LOGGER.info(f"{tag} ({len(cbx)}): {cbx.match(permutation, cube_size=cube_size)}")


def create_single_cubex() -> None:
    cube_size = 3
    generator = MoveGenerator("<F2, B2, L, R, U, D>")

    LOGGER.info("\nCreating single cubex for eo_fb:")
    eo_fb = CubexCollection.from_settings(
        pieces=[Piece.edge.value], generator=generator, cube_size=cube_size
    )

    LOGGER.info(eo_fb.cubexes[0].mask)
    LOGGER.info(eo_fb.cubexes[0].pattern)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # test_main()
    test_main_simple()
