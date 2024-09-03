import numpy as np

from rubiks_cube.configuration import CUBE_SIZE
from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.state import get_rubiks_cube_state
from rubiks_cube.state.permutation import create_permutations
from rubiks_cube.state.permutation.tracing import corner_trace
from rubiks_cube.state.tag.patterns import get_cubexes


def autotag_state(state: np.ndarray, default_tag: str = "none") -> str:
    """
    Tag the state from the given permutation state.
    1. Find the tag corresponding to the state.
    2. Post-process the tag if necessary.
    """

    if CUBE_SIZE != 3:
        return "none"

    for tag, cbx in get_cubexes().items():
        if cbx.match(state):
            return_tag = tag
            break
    else:
        return_tag = default_tag

    # TODO: This code works, but should be replaced w non-stochastic method!
    # If uses on average ~2 moves to differentiate between real/fake HTR
    # It recognizes if it is real/fake HTR by corner-tracing
    if return_tag == "htr-like":
        real_htr_traces = ["", "2c2c2c2c"]
        fake_htr_traces = [
            "3c2c2c",
            "2c2c2c",
            "4c3c",
            "4c",
            "2c",
            "3c2c",
            "4c2c2c",
            "3c",
        ]  # noqa: #501
        # real/fake = ['3c3c', '4c2c', '2c2c', '4c4c']

        rng = np.random.default_rng(seed=42)
        permutations = create_permutations()
        temp_state = np.copy(state)
        while return_tag == "htr-like":
            trace = corner_trace(temp_state)
            if trace in real_htr_traces:
                return_tag = "htr"
            elif trace in fake_htr_traces:
                return_tag = "fake-htr"
            else:
                move = rng.choice(["L2", "R2", "U2", "D2", "F2", "B2"], size=1)[0]  # noqa: E501
                temp_state = temp_state[permutations[move]]

    return return_tag


def autotag_step(initial_state: np.ndarray, final_state: np.ndarray) -> str:
    """Tag the step from the given states."""

    if np.array_equal(initial_state, final_state):
        return "rotation"

    initial_tag = autotag_state(initial_state)
    final_tag = autotag_state(final_state)

    step_dict = {
        "none -> eo": "eo",
        "none -> cross": "cross",
        "none -> x-cross": "x-cross",
        "none -> xx-cross": "xx-cross",
        "none -> xxx-cross": "xxx-cross",
        "none -> f2l": "xxxx-cross",
        "eo -> eo": "drm",
        "eo -> dr": "dr",
        "dr -> htr": "htr",
        "dr -> fake-htr": "fake-htr",
        "htr -> solved": "solved",
        "cross -> x-cross": "first-pair",
        "x-cross -> xx-cross": "second-pair",
        "xx-cross -> xxx-cross": "third-pair",
        "x-cross -> xxx-cross": "second-pair + third-pair",
        "xx-cross -> f2l": "last-pair",
        "xxx-cross -> f2l": "fourth-pair",
        "xxx-cross -> f2l-eo": "fourth-pair + eo",
        "xxx-cross -> f2l-ep-co": "fourth-pair + oll",
        "xxx-cross -> f2l-face": "fourth-pair + oll",
        "f2l -> f2l-face": "oll",
        "f2l -> solved": "ll",
        "f2l -> f2l-layer": "oll + pll",
        "f2l-face -> f2l-layer": "pll",
        "f2l-face -> solved": "pll",
        "f2l-eo -> f2l-face": "oll",
        "f2l-eo -> f2l-layer": "zbll",
        "f2l-eo -> solved": "zbll",
        "f2l-layer -> solved": "auf",
        "f2l-ep-co -> f2l-layer": "pll",
        "f2l-ep-co -> solved": "pll",
    }

    step = f"{initial_tag} -> {final_tag}"

    return step_dict.get(step, step)


if __name__ == "__main__":
    import numpy as np

    # from rubiks_cube.state.permutation import create_permutations

    test_state = get_rubiks_cube_state(
        MoveSequence("R' U L' U2 R U' R' L U L' U2 R U' L U R2")
        # + MoveSequence("R' U L' U2 R U' R' L U L' U2 R U' L U")
    )
    print("Tag:", autotag_state(test_state))

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

    print("Average checks: ", sum(n_checks) / n)
    print("Maximum checks: ", max(n_checks))

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

    print("Real HTR corner traces:", real_set)
    print("Fake HTR (2-swap) corner traces:", fake_set2)
    print("Fake HTR (3-swap) corner traces:", fake_set3)

    print("Definitive real:", real_set - fake_set)
    print("Definitive fake:", fake_set - real_set)
    print("Either:", real_set.union(fake_set) - (fake_set - real_set) - (real_set - fake_set))  # noqa: #501
    """
