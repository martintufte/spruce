import logging
from typing import Final

from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.representation import get_rubiks_cube_state
from rubiks_cube.tag import autotag_permutation

LOGGER: Final = logging.getLogger(__name__)


def test_main() -> None:
    state = get_rubiks_cube_state(MoveSequence("R' U L' U2 R U' R' L U L' U2 R U' L U R2"))
    autotag_permutation(state)
