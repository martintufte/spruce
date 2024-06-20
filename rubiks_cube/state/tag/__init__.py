import numpy as np

from rubiks_cube.state.tag.patterns import get_cubexes
from rubiks_cube.state.permutation.tracing import corner_trace
from rubiks_cube.configuration import CUBE_SIZE


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

    # TODO: This HTR distinction is not very good.
    if return_tag == "htr-like":
        htr_corner_traces = ["", "3c3c", "2c2c", "4c4c", "4c2c", "2c2c2c2c"]
        if corner_trace(state) in htr_corner_traces:
            return_tag = "htr"
        else:
            return_tag = "fake-htr"

    return return_tag


def autotag_step(
    initial_state: np.ndarray,
    final_state: np.ndarray,
) -> str:
    """
    Tag the step from the given permutation state.
    """

    initial_tag = autotag_state(initial_state)
    final_tag = autotag_state(final_state)

    step_dict = {
        "none -> eo": "eo",
        "eo -> eo": "drm",
        "eo -> dr": "dr",
        "dr -> htr": "htr",
        "htr -> solved": "solved",
        "none -> none": "inspection",
        "none -> cross": "cross",
        "none -> x-cross": "x-cross",
        "none -> xx-cross": "xx-cross",
        "none -> xxx-cross": "xxx-cross",
        "none -> f2l": "xxxx-cross",
        "cross -> x-cross": "first-pair",
        "x-cross -> xx-cross": "second-pair",
        "xx-cross -> xxx-cross": "third-pair",
        "xxx-cross -> f2l": "fourth-pair",
        "f2l -> f2l-face": "oll",
        "f2l -> solved": "ll",
        "f2l-face -> f2l-layer": "pll",
        "f2l-face -> solved": "pll",
        "f2l-eo -> solved": "zbll",
        "f2l-layer -> solved": "auf",
    }

    step = f"{initial_tag} -> {final_tag}"

    return step_dict.get(step, step)
