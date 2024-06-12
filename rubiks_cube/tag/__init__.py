from rubiks_cube.utils.sequence import Sequence
from rubiks_cube.tag.patterns import get_cubex
from rubiks_cube.tag.patterns import Cubex


def autotag(scramble: Sequence, normal: Sequence, inverse: Sequence) -> str:
    """
    Tag the state with the given step
    """
    raise NotImplementedError


def autotag_sequence() -> dict[str, Cubex]:
    """
    Tag the state with the given permutation
    """
    return get_cubex()
