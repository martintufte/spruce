import numpy as np

from rubiks_cube.tag.patterns import get_cubexes


def autotag_state(permutation: np.ndarray, default_tag: str = "none") -> str:
    """
    Tag the state from the given permutation state.
    """
    cubexes = get_cubexes()

    for tag, cbx in cubexes.items():
        if cbx.match(permutation):
            return tag
    return default_tag


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
