import re

from rubiks_cube.configuration import CUBE_SIZE
from rubiks_cube.configuration.type_definitions import CubePermutation
from rubiks_cube.move.generator import MoveGenerator
from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.state import get_rubiks_cube_state
from rubiks_cube.state.permutation import create_permutations


def get_action_space(
    generator: MoveGenerator,
    cube_size: int = CUBE_SIZE,
) -> dict[str, CubePermutation]:
    """Get the action space from a generator.

    Args:
        generator (MoveGenerator): Move generator.
        cube_size (int): Size of the cube.

    Returns:
        dict[str, CubePermutation]: Action space.
    """

    actions = {}
    for sequence in generator:
        for sequence in expand_generator(sequence, cube_size=cube_size):
            permutation = get_rubiks_cube_state(
                sequence=sequence,
                cube_size=cube_size,
            )
            actions[str(sequence)] = permutation
    return actions


def expand_generator(sequence: MoveSequence, cube_size: int) -> list[MoveSequence]:
    """This function expands a sequence into a list of sequences if the move is
    a sequence of length one and the move is in the permutations and the move
    is not a double move.

    Args:
        sequence (MoveSequence): The move sequence to expand.

    Returns:
        list[str]: List of expanded move sequences.
    """
    permutations = create_permutations(cube_size=cube_size)

    if len(sequence.moves) != 1:
        return [sequence]

    move = sequence.moves[0]
    if move not in permutations:
        return [sequence]

    pattern = re.compile(r"^([23456789]?[LRFBUD][w])(['2]?)$|^([LRFBUDxyzMES])(['2]?)$")
    match = pattern.match(move)

    if match is not None:
        core = match.group(1) or match.group(3)
        modifier = match.group(2) or match.group(4)

        if modifier == "2":
            return [sequence]

        return [
            MoveSequence(f"{core}"),
            MoveSequence(f"{core}'"),
            MoveSequence(f"{core}2"),
        ]

    return [sequence]
