import numpy as np

from rubiks_cube.tag.patterns import get_cubexes
from rubiks_cube.state.permutation.tracing import corner_trace


def autotag_state(permutation: np.ndarray, default_tag: str = "none") -> str:
    """
    Tag the state from the given permutation state.
    1. Find the tag corresponding to the state.
    2. Post-process the tag if necessary.
    """

    for tag, cbx in get_cubexes().items():
        if cbx.match(permutation):
            return_tag = tag
            break
    else:
        return_tag = default_tag

    # TODO: Dobule-check the differentiating criteria
    if return_tag == "htr-like":
        htr_corner_traces = ["", "3c3c", "2c2c", "4c4c", "4c2c", "2c2c2c2c"]
        if corner_trace(permutation) in htr_corner_traces:
            return_tag = "htr"
        else:
            return_tag = "fake-htr"

    return return_tag


def autotag_step(
    start_permutation: np.ndarray,
    end_permutation: np.ndarray,
    default_tag: str = "?"
) -> str:
    """
    Tag the step from the given permutation state.
    """

    start_tag = autotag_state(start_permutation)
    end_tag = autotag_state(end_permutation)

    return f"{start_tag} -> {end_tag}"
