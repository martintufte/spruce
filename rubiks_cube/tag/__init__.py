import numpy as np

from rubiks_cube.configuration import CUBE_SIZE
from rubiks_cube.configuration.type_definitions import CubeState
from rubiks_cube.state.permutation import create_permutations
from rubiks_cube.state.tracing import corner_trace
from rubiks_cube.tag.cubex import get_cubexes


def autotag_state(state: CubeState, default_tag: str = "none") -> str:
    """Tag the state from the given permutation state.
    1. Find the tag corresponding to the state.
    2. Post-process the tag if necessary.

    Args:
        state (CubeState): Cube state.
        default_tag (str, optional): Dafualt tag. Defaults to "none".

    Returns:
        str: Tag of the state.
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
        ]
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
                move = rng.choice(["L2", "R2", "U2", "D2", "F2", "B2"], size=1)[0]
                temp_state = temp_state[permutations[move]]

    return return_tag


def autotag_step(initial_state: CubeState, final_state: CubeState) -> str:
    """Tag the step from the given states.

    Args:
        initial_state (CubeState): Initial state.
        final_state (CubeState): Final state.

    Returns:
        str: Tag of the step.
    """

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
