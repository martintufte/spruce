import logging
from typing import Final

from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.state import get_rubiks_cube_state
from rubiks_cube.tag import autotag_permutation

LOGGER: Final = logging.getLogger(__name__)


def test_main() -> None:
    state = get_rubiks_cube_state(MoveSequence("R' U L' U2 R U' R' L U L' U2 R U' L U R2"))
    autotag_permutation(state)


def test_check_number_of_moves() -> None:
    """
    # Code for checing the number of moves to differentiate between real/fake
    rng = np.random.default_rng(seed=42)
    permutations = create_permutations()
    n = 1000

    n_checks = []
    for move in rng.choice(["L2", "R2", "U2", "D2", "F2", "B2"], size=n):
        test_state = test_state[permutations[move]]
        try:
            n_checks.append(int(autotag_state(test_state)))
        except Exception:
            n_checks.append(0)

    LOGGER.info("Average checks: ", sum(n_checks) / n)
    LOGGER.info("Maximum checks: ", max(n_checks))

    # Code for finding the set of corner traces for real and fake HTR

    # Find the unique corner traces of real, 2-swap or 3-swap htr
    real_htr_traces = []
    fake_htr2_traces = []
    fake_htr3_traces = []

    real_state = get_rubiks_cube_state(
        MoveSequence("")
    )
    fake2_state = get_rubiks_cube_state(
        MoveSequence("R' U L' U2 R U' R' L U L' U2 R U' L U")
    )
    fake3_state = get_rubiks_cube_state(
        MoveSequence("R' U L' U2 R U' R' L U L' U2 R U' L U")
        + MoveSequence("R2")
        + MoveSequence("R' U L' U2 R U' R' L U L' U2 R U' L U")
    )

    for move in rng.choice(["L2", "R2", "U2", "D2", "F2", "B2"], size=1000):
        real_state = real_state[permutations[move]]
        real_htr_traces.append(corner_trace(real_state))

        fake2_state = fake2_state[permutations[move]]
        fake_htr2_traces.append(corner_trace(fake2_state))

        fake3_state = fake3_state[permutations[move]]
        fake_htr3_traces.append(corner_trace(fake3_state))

    real_set = set(real_htr_traces)
    fake_set2 = set(fake_htr2_traces)
    fake_set3 = set(fake_htr3_traces)
    fake_set = set(fake_htr2_traces).union(set(fake_htr3_traces))

    LOGGER.info("Real HTR corner traces:", real_set)
    LOGGER.info("Fake HTR (2-swap) corner traces:", fake_set2)
    LOGGER.info("Fake HTR (3-swap) corner traces:", fake_set3)

    LOGGER.info("Definitive real:", real_set - fake_set)
    LOGGER.info("Definitive fake:", fake_set - real_set)
    LOGGER.info("Either:", real_set.union(fake_set) - (fake_set - real_set) - (real_set - fake_set))  # noqa: #501
    """
