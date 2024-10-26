import logging
from typing import Final

from rubiks_cube.attempt import FewestMovesAttempt

LOGGER: Final = logging.getLogger(__name__)


def test_fewest_moves_attempt() -> None:
    scramble_input = """
    R' U' F L U B' D' L F2 U2 D' B U R2 D F2 R2 F2 L2 D' F2 D2 R' U' F
    """
    attempt_input = """
    B' (F2 R' F)
    (L')
    R2 L2 F2 D' B2 D B2 U' R'
    U F2 * U2 B2 R2 U'
    * = L2
    B2 L2 D2 R2 D2 L2
    """

    attempt = FewestMovesAttempt.from_string(scramble_input, attempt_input)
    attempt.compile()

    LOGGER.info("Attempt:")
    LOGGER.info(attempt)

    for step, tag, subset, moves, cancels, total in attempt:
        if cancels > 0:
            LOGGER.info(f"{step}  // {tag} ({moves}-{cancels}/{total})")
        else:
            LOGGER.info(f"{step}  // {tag} ({moves}/{total})")

    scramble_input = """
    D R' U2 F2 D U' B2 R2 L' F U' B2 U2 F L F' D'
    """
    attempt_input = """
    x2
    R' D2 R' D L' U L D R' U' R D
    L U' L'
    U' R U R' y' U R' U' R
    r' U' R U' R' U2 r
    U
    """
    attempt = FewestMovesAttempt.from_string(scramble_input, attempt_input)
    attempt.compile()

    LOGGER.info("Attempt:")
    LOGGER.info(attempt)
