import numpy as np
import numpy.testing as npt

from rubiks_cube.move.generator import MoveGenerator
from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.state.permutation import create_mask_from_sequence
from rubiks_cube.state.permutation import generate_indices_symmetries
from rubiks_cube.state.permutation import generate_mask_symmetries
from rubiks_cube.state.permutation import generate_permutation_symmetries
from rubiks_cube.state.permutation import indices2ordered_mask
from rubiks_cube.state.permutation import ordered_mask2indices


def test_generate_mask_symmetries() -> None:
    # Test the create_permutations function
    sequence = MoveSequence("U R")
    generator = MoveGenerator("<x, y>")
    mask = create_mask_from_sequence(sequence)

    group = generate_mask_symmetries(masks=[mask], generator=generator)
    assert len(group) == 12


def test_generate_indices_symmetries() -> None:
    # Test that generate_statemask_symmetries works
    sequence = MoveSequence("Dw")
    generator = MoveGenerator("<U>")
    mask = create_mask_from_sequence(sequence)

    states = generate_indices_symmetries(mask, generator)
    assert len(states) == 4


def test_indecies2ordered_mask() -> None:
    # Test indices2ordered_mask and ordered_mask2indices
    indices = np.array([1, 5, 3, 7, 9])
    mask = indices2ordered_mask(indices)
    npt.assert_equal(ordered_mask2indices(mask), indices)


def test_generate_permutation_symmetries() -> None:
    # Test generate_permutation_symmetries
    mask = create_mask_from_sequence(MoveSequence("Dw Rw"))
    generator = MoveGenerator("<F, B>")
    permutations = generate_permutation_symmetries(mask, generator)
    assert len(permutations) == 16
