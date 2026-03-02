from __future__ import annotations

from typing import TYPE_CHECKING
from typing import cast

import numpy as np
import pytest

from rubiks_cube.representation.permutation import create_permutations
from rubiks_cube.representation.permutation import get_identity_permutation
from rubiks_cube.representation.utils import conjugate
from rubiks_cube.representation.utils import invert
from rubiks_cube.representation.utils import multiply
from rubiks_cube.representation.utils import reindex
from rubiks_cube.representation.utils import rotate_face
from tests.conftest import is_permutation

if TYPE_CHECKING:
    from rubiks_cube.configuration.types import CubePermutation


def create_random_permutation(
    cube_size: int, rng: np.random.Generator | None = None
) -> CubePermutation:
    if rng is None:
        rng = np.random.default_rng()

    return cast("CubePermutation", rng.permutation(6 * cube_size**2))


class TestRotateFace:
    """Test rotate_face function."""

    def test_rotate_face_3x3_once(self) -> None:
        # Create a 3x3 face with distinct values
        perm = get_identity_permutation(cube_size=3)
        face = slice(0, 9)  # First face (Up)

        rotated = rotate_face(perm, face, 1)

        # Check that rotation is correct
        original_face = perm[face].reshape(3, 3)
        expected = np.rot90(original_face, 1).flatten()
        assert np.array_equal(rotated, expected)

    def test_rotate_face_3x3_twice(self) -> None:
        perm = get_identity_permutation(cube_size=3)
        face = slice(0, 9)

        rotated = rotate_face(perm, face, 2)

        original_face = perm[face].reshape(3, 3)
        expected = np.rot90(original_face, 2).flatten()
        assert np.array_equal(rotated, expected)

    def test_rotate_face_3x3_four_times(self) -> None:
        perm = get_identity_permutation(cube_size=3)
        face = slice(0, 9)

        rotated = rotate_face(perm, face, 4)

        # Four rotations should return to original
        original_face = perm[face]
        assert np.array_equal(rotated, original_face)

    def test_rotate_face_2x2(self) -> None:
        perm = get_identity_permutation(cube_size=2)
        face = slice(0, 4)  # First face (Up)

        rotated = rotate_face(perm, face, 1)

        original_face = perm[face].reshape(2, 2)
        expected = np.rot90(original_face, 1).flatten()
        assert np.array_equal(rotated, expected)

    def test_rotate_face_negative_rotation(self) -> None:
        perm = get_identity_permutation(cube_size=3)
        face = slice(0, 9)

        rotated_neg = rotate_face(perm, face, -1)
        rotated_pos = rotate_face(perm, face, 3)

        # -1 rotation should equal 3 positive rotations
        assert np.array_equal(rotated_neg, rotated_pos)


class TestInvert:
    """Test invert function."""

    def test_invert_identity(self) -> None:
        identity = get_identity_permutation(cube_size=3)
        inverted = invert(identity)

        # Inverse of identity should be identity
        assert np.array_equal(inverted, identity)
        assert is_permutation(inverted)

    def test_invert_simple_permutation(self) -> None:
        # Create a simple permutation: [1, 0, 2]
        perm = np.array([1, 0, 2])
        inverted = invert(perm)

        # Inverse should be [1, 0, 2] (self-inverse)
        expected = np.array([1, 0, 2])
        assert np.array_equal(inverted, expected)
        assert is_permutation(inverted)

    def test_invert_cycle(self) -> None:
        # Create a 3-cycle: [1, 2, 0]
        perm = np.array([1, 2, 0])
        inverted = invert(perm)

        # Inverse of [1, 2, 0] should be [2, 0, 1]
        expected = np.array([2, 0, 1])
        assert np.array_equal(inverted, expected)
        assert is_permutation(inverted)

    def test_invert_composition_identity(self) -> None:
        # Test that perm * invert(perm) = identity
        identity = get_identity_permutation(cube_size=3)
        # Create a non-trivial permutation
        perm = create_random_permutation(cube_size=3)
        inverted = invert(perm)

        # Apply permutation then its inverse
        result = identity[perm][inverted]
        assert np.array_equal(result, identity)

    def test_invert_involution(self) -> None:
        # Test that invert(invert(perm)) = perm
        perm = create_random_permutation(cube_size=2)
        double_inverted = invert(invert(perm))
        assert np.array_equal(double_inverted, perm)

    def test_invert_preserves_permutation_property(self) -> None:
        # Test on various cube sizes
        for cube_size in [1, 2, 3, 4]:
            perm = create_random_permutation(cube_size=cube_size)
            inverted = invert(perm)

            assert is_permutation(inverted)


class TestMultiply:
    """Test multiply function."""

    def test_multiply_identity(self) -> None:
        identity = get_identity_permutation(cube_size=3)

        for factor in [1, 2, 3, 4, 5]:
            result = multiply(identity, factor)
            assert np.array_equal(result, identity)

    def test_multiply_simple_cycle(self) -> None:
        # Create a 4-cycle: [1, 2, 3, 0]
        base = np.array([1, 2, 3, 0])

        # Test various powers
        result1 = multiply(base, 1)
        assert np.array_equal(result1, base)

        result2 = multiply(base, 2)
        expected2 = np.array([2, 3, 0, 1])
        assert np.array_equal(result2, expected2)

        result4 = multiply(base, 4)
        expected4 = np.array([0, 1, 2, 3])  # Should be identity
        assert np.array_equal(result4, expected4)

    def test_multiply_preserves_permutation_property(self) -> None:
        base = create_random_permutation(cube_size=1)

        for factor in [1, 2, 3, 4, 5]:
            result = multiply(base, factor)
            assert is_permutation(result)

    def test_zero_factor(self) -> None:
        base = np.array([1, 0, 2, 3])

        result = multiply(base, 0)
        expected = np.array([0, 1, 2, 3])
        assert np.array_equal(result, expected)

    def test_multiply_invalid_factor(self) -> None:
        base = create_random_permutation(cube_size=1)

        with pytest.raises(AssertionError):
            multiply(base, -1)

    def test_multiply_composition_property(self) -> None:
        # Test that multiply(perm, a) * multiply(perm, b) = multiply(perm, a+b) for simple cases
        perm = np.array([1, 2, 0, 3])  # 3-cycle + fixed point
        identity = np.arange(4)

        # Test multiply(perm, 2) composed twice equals multiply(perm, 4)
        mult2 = multiply(perm, 2)
        mult2_twice = identity[mult2][mult2]
        mult4 = multiply(perm, 4)

        assert np.array_equal(mult2_twice, mult4)


class TestReindex:
    """Test reindex function."""

    def test_reindex_all_true_mask(self) -> None:
        perm = np.array([2, 1, 0, 4, 3])
        mask = np.ones(5, dtype=bool)

        result = reindex(perm, mask)

        # With all-true mask, should reindex to [0, 1, 2, 3, 4] order
        # Original: [2, 1, 0, 4, 3] -> indices get mapped to positions
        expected = np.array([2, 1, 0, 4, 3])
        assert np.array_equal(result, expected)

    def test_reindex_partial_mask(self) -> None:
        perm = np.array([0, 1, 2, 3, 4])  # Identity
        mask = np.array([True, False, True, False, True])

        result = reindex(perm, mask)

        # Should extract positions 0, 2, 4 and reindex them as 0, 1, 2
        expected = np.array([0, 1, 2])
        assert np.array_equal(result, expected)

    def test_reindex_simple_case(self) -> None:
        # Test documented assumption: perm[~mask] == id[~mask]
        perm = np.array([0, 3, 2, 1, 4])  # Swap positions 1 and 3
        mask = np.array([False, True, False, True, False])

        # perm[mask] = [3, 1], these should be reindexed
        result = reindex(perm, mask)

        # Position 1 -> value 3, position 3 -> value 1
        # After reindexing: 3->1, 1->0
        expected = np.array([1, 0])
        assert np.array_equal(result, expected)

    def test_reindex_preserves_relative_order(self) -> None:
        perm = np.array([1, 0, 3, 2, 4])
        mask = np.array([True, True, False, False, False])

        result = reindex(perm, mask)

        # Extract [1, 0] and reindex: 1->1, 0->0
        expected = np.array([1, 0])
        assert np.array_equal(result, expected)

    def test_reindex_empty_mask(self) -> None:
        perm = np.array([1, 0, 2])
        mask = np.array([False, False, False])

        result = reindex(perm, mask)

        # Empty mask should return empty array
        assert len(result) == 0

    def test_reindex_single_element(self) -> None:
        perm = np.array([0, 1, 2, 3])
        mask = np.array([False, False, True, False])

        result = reindex(perm, mask)

        # Extract position 2 (value 2) and reindex to 0
        expected = np.array([0])
        assert np.array_equal(result, expected)


class TestConjugate:
    """Test conjugate function."""

    def test_conjugate_identity_g(self) -> None:
        perm = np.array([1, 0, 3, 2])
        identity = np.arange(4, dtype=np.uint)

        result = conjugate(perm, identity)

        assert is_permutation(result)
        assert np.array_equal(result, perm)

    def test_conjugate_matches_formula(self) -> None:
        perm = create_random_permutation(cube_size=1)
        g = create_random_permutation(cube_size=1)

        expected = g[perm][invert(g)]
        result = conjugate(perm, g)

        assert is_permutation(result)
        assert np.array_equal(result, expected)

    def test_conjugate_matches_cube_rotation_relations(self) -> None:
        perms = create_permutations(cube_size=3)

        assert np.array_equal(conjugate(perms["y"], perms["x"]), perms["z"])
        assert np.array_equal(conjugate(perms["U"], perms["x"]), perms["F"])


class TestUtilsIntegration:
    """Test integration between utility functions."""

    def test_invert_multiply_composition(self) -> None:
        # Test that multiply(invert(perm), n) = invert(multiply(perm, n))
        perm = np.array([1, 2, 0, 3])  # 3-cycle + fixed point

        for n in [1, 2, 3]:
            mult_inv = multiply(invert(perm), n)
            inv_mult = invert(multiply(perm, n))
            assert np.array_equal(mult_inv, inv_mult)

    def test_rotate_face_with_reindex(self) -> None:
        # Test that rotating and then reindexing works correctly
        identity = get_identity_permutation(cube_size=3)
        face = slice(0, 9)

        rotated = rotate_face(identity, face, 1)
        mask = np.ones(9, dtype=bool)

        # This should work without error
        reindexed = reindex(rotated, mask)
        assert len(reindexed) == 9

    def test_all_utils_preserve_array_properties(self) -> None:
        # Test that all utilities preserve basic numpy array properties
        perm = get_identity_permutation(cube_size=3)

        # Test invert
        inverted = invert(perm)
        assert inverted.dtype == perm.dtype
        assert inverted.shape == perm.shape

        # Test multiply
        multiplied = multiply(perm, 2)
        assert multiplied.dtype == perm.dtype
        assert multiplied.shape == perm.shape

        # Test rotate_face
        rotated = rotate_face(perm, slice(0, 9), 1)
        assert rotated.dtype == perm.dtype
        assert len(rotated) == 9
