from rubiks_cube.utils.sequence import Sequence
from rubiks_cube.tag.patterns import get_cubex


def autotag(scramble: Sequence, normal: Sequence, inverse: Sequence) -> str:
    """
    Tag the state with the given step
    """
    raise NotImplementedError


def autotag_sequence(sequence: Sequence) -> str:
    """
    Tag the state with the given permutation
    """
    cbxs = get_cubex()
    return_str = ""
    for tag, cbx in sorted(cbxs.items()):
        return_str += f"{tag} ({len(cbx)}): " + str(cbx.match(sequence)) + "\n"

    return return_str
