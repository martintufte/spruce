import numpy as np

from rubiks_cube.move.generator import MoveGenerator
from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.state.permutation import create_mask_from_sequence
from rubiks_cube.state.permutation import generate_indices_symmetries
from rubiks_cube.state.permutation import generate_mask_symmetries
from rubiks_cube.state.permutation import generate_permutation_symmetries
from rubiks_cube.state.permutation import indices2ordered_mask
from rubiks_cube.state.permutation import ordered_mask2indices


def test_main() -> None:
    # Test the create_permutations function
    sequence = MoveSequence("U R")
    generator = MoveGenerator("<x, y>")
    mask = create_mask_from_sequence(sequence)

    group = generate_mask_symmetries(masks=[mask], generator=generator)
    print(f'"{sequence}" has symmetry-group of length {len(group)}')

    # Test that generate_statemask_symmetries works
    sequence = MoveSequence("Dw")
    generator = MoveGenerator("<U>")
    mask = create_mask_from_sequence(sequence)

    states = generate_indices_symmetries(mask, generator)
    print(states)
    print(f"Generated {len(states)} states")

    # Test indices2ordered_mask and ordered_mask2indices
    indices = np.array([1, 5, 3, 7, 9])
    mask = indices2ordered_mask(indices)
    print(mask)
    print(ordered_mask2indices(mask))

    # Test generate_permutation_symmetries
    mask = create_mask_from_sequence(MoveSequence("Dw Rw"))
    generator = MoveGenerator("<F, B>")
    permutations = generate_permutation_symmetries(mask, generator)
    print(permutations)
    print(f"Generated {len(permutations)} permutations")
