import logging
from typing import Final

from rubiks_cube.autotagger import autotag_permutation
from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.representation import get_rubiks_cube_state

LOGGER: Final = logging.getLogger(__name__)


class TestAutoTagger:
    def test(self) -> None:
        permutation = get_rubiks_cube_state(
            MoveSequence("R' U L' U2 R U' R' L U L' U2 R U' L U R2")
        )
        autotag_permutation(permutation)

    def test_htr(self) -> None:
        state = get_rubiks_cube_state(MoveSequence("R2 U2 F2"))
        autotag_permutation(state)
