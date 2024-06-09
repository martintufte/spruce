import numpy as np

from rubiks_cube.utils.sequence import Sequence


def autotag(scramble: Sequence, normal: Sequence, inverse: Sequence) -> str:
    """
    Tag the state with the given step
    """
    raise NotImplementedError


def autotag_permutation(permutation: np.ndarray) -> str:
    """
    Tag the state with the given permutation
    """
    raise NotImplementedError
