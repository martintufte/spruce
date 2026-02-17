import logging
from typing import Final

from rubiks_cube.attempt import Attempt
from rubiks_cube.move.meta import MoveMeta
from rubiks_cube.parsing import parse_scramble
from rubiks_cube.parsing import parse_steps

LOGGER: Final = logging.getLogger(__name__)


def test_fewest_moves_attempt() -> None:
    scramble_input = """
    R' U' F L U B' D' L F2 U2 D' B U R2 D F2 R2 F2 L2 D' F2 D2 R' U' F
    """
    steps_input = """
    B' (F2 R' F)
    (L')
    R2 L2 F2 D' B2 D B2 U' R'
    U F2 * U2 B2 R2 U'
    * = L2
    B2 L2 D2 R2 D2 L2
    """

    move_meta = MoveMeta.from_cube_size(3)
    attempt = Attempt(
        scramble=parse_scramble(scramble_input),
        steps=parse_steps(steps_input),
        move_meta=move_meta,
    )
    attempt.compile()

    LOGGER.info("Attempt:")
    LOGGER.info(attempt)

    for step, pattern, _subset, moves, cancels, total in attempt:
        if cancels > 0:
            LOGGER.info(f"{step}  // {pattern} ({moves}-{cancels}/{total})")
        else:
            LOGGER.info(f"{step}  // {pattern} ({moves}/{total})")

    scramble_input = """
    D R' U2 F2 D U' B2 R2 L' F U' B2 U2 F L F' D'
    """
    steps_input = """
    x2
    R' D2 R' D L' U L D R' U' R D
    L U' L'
    U' R U R' y' U R' U' R
    r' U' R U' R' U2 r
    U
    """
    attempt = Attempt(
        scramble=parse_scramble(scramble_input),
        steps=parse_steps(steps_input),
        move_meta=move_meta,
    )
    attempt.compile()

    LOGGER.info("Attempt:")
    LOGGER.info(attempt)
