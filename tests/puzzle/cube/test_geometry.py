from __future__ import annotations

import numpy as np

from spruce.algebra.permutation import get_identity
from spruce.puzzle.cube.geometry import create_permutations
from spruce.puzzle.cube.geometry import rotate_face
from spruce.types import MoveSymbol
from tests.conftest import is_permutation


class TestRotateFace:
    """Test rotate_face function."""

    def test_rotate_face_3x3_once(self) -> None:
        # Create a 3x3 face with distinct values
        perm = get_identity(size=54)
        face = slice(0, 9)  # First face (Up)

        rotated = rotate_face(perm, face, 1)

        # Check that rotation is correct
        original_face = perm[face].reshape(3, 3)
        expected = np.rot90(original_face, 1).flatten()
        assert np.array_equal(rotated, expected)

    def test_rotate_face_3x3_twice(self) -> None:
        perm = get_identity(size=54)
        face = slice(0, 9)

        rotated = rotate_face(perm, face, 2)

        original_face = perm[face].reshape(3, 3)
        expected = np.rot90(original_face, 2).flatten()
        assert np.array_equal(rotated, expected)

    def test_rotate_face_3x3_four_times(self) -> None:
        perm = get_identity(size=54)
        face = slice(0, 9)

        rotated = rotate_face(perm, face, 4)

        # Four rotations should return to original
        original_face = perm[face]
        assert np.array_equal(rotated, original_face)

    def test_rotate_face_2x2(self) -> None:
        perm = get_identity(size=24)
        face = slice(0, 4)  # First face (Up)

        rotated = rotate_face(perm, face, 1)

        original_face = perm[face].reshape(2, 2)
        expected = np.rot90(original_face, 1).flatten()
        assert np.array_equal(rotated, expected)

    def test_rotate_face_negative_rotation(self) -> None:
        perm = get_identity(size=54)
        face = slice(0, 9)

        rotated_neg = rotate_face(perm, face, -1)
        rotated_pos = rotate_face(perm, face, 3)

        # -1 rotation should equal 3 positive rotations
        assert np.array_equal(rotated_neg, rotated_pos)


class TestGetIdentityPermutation:
    """Test get_identity function."""

    def test_identity_3x3(self) -> None:
        identity = get_identity(size=54)
        expected = np.arange(54)
        assert np.array_equal(identity, expected)
        assert is_permutation(identity)

    def test_identity_2x2(self) -> None:
        identity = get_identity(size=24)
        expected = np.arange(24)
        assert np.array_equal(identity, expected)
        assert is_permutation(identity)

    def test_identity_4x4(self) -> None:
        identity = get_identity(size=96)
        expected = np.arange(96)
        assert np.array_equal(identity, expected)
        assert is_permutation(identity)

    def test_identity_1x1(self) -> None:
        identity = get_identity(size=6)
        expected = np.arange(6)
        assert np.array_equal(identity, expected)
        assert is_permutation(identity)


class TestCreatePermutations:
    """Test create_permutations function."""

    def test_create_permutations_3x3(self) -> None:
        permutations = create_permutations(cube_size=3)
        identity = get_identity(size=54)

        # Test identity
        assert np.array_equal(permutations[MoveSymbol("I")], identity)

        # Test all permutations are valid
        for perm in permutations.values():
            assert is_permutation(perm)
            assert len(perm) == 54

    def test_create_permutations_2x2(self) -> None:
        perms = create_permutations(cube_size=2)
        identity = get_identity(size=24)

        # Test identity
        assert np.array_equal(perms[MoveSymbol("I")], identity)

        # Test all permutations are valid
        for perm in perms.values():
            assert is_permutation(perm)
            assert len(perm) == 24

    def test_basic_moves_present(self) -> None:
        permutations = create_permutations(cube_size=3)

        # Test basic face moves are present
        basic_symbols = [
            "U",
            "U'",
            "U2",
            "R",
            "R'",
            "R2",
            "F",
            "F'",
            "F2",
            "L",
            "L'",
            "L2",
            "B",
            "B'",
            "B2",
            "D",
            "D'",
            "D2",
        ]
        for symbol in basic_symbols:
            assert symbol in permutations

        # Test rotations are present
        rotations = ["x", "x'", "x2", "y", "y'", "y2", "z", "z'", "z2"]
        for rotation in rotations:
            assert rotation in permutations

    def test_slice_moves_3x3(self) -> None:
        permutations = create_permutations(cube_size=3)

        # Test slice moves for 3x3
        slice_symbols = ["M", "M'", "M2", "E", "E'", "E2", "S", "S'", "S2"]
        for symbol in slice_symbols:
            assert symbol in permutations

    def test_no_slice_moves_2x2(self) -> None:
        permutations = create_permutations(cube_size=2)

        # Test slice moves are not present for 2x2
        slice_symbols = ["M", "M'", "M2", "E", "E'", "E2", "S", "S'", "S2"]
        for symbol in slice_symbols:
            assert symbol not in permutations

    def test_wide_moves(self) -> None:
        permutations = create_permutations(cube_size=3)

        # Test wide moves are present
        wide_symbols = ["Uw", "Uw'", "Uw2", "Rw", "Rw'", "Rw2"]
        for symbol in wide_symbols:
            assert symbol in permutations

    def test_move_inverses(self) -> None:
        permutations = create_permutations(cube_size=3)
        identity = get_identity(size=54)

        # Test that move and its inverse compose to identity
        test_symbols = ["U", "R", "F", "x", "y"]
        for raw_symbol in test_symbols:
            symbol = MoveSymbol(raw_symbol)
            symbol_inv = MoveSymbol(raw_symbol + "'")
            if symbol_inv in permutations:
                # Apply move then its inverse
                result = identity[permutations[symbol]][permutations[symbol_inv]]
                assert np.array_equal(result, identity)

    def test_move_doubles(self) -> None:
        permutations = create_permutations(cube_size=3)
        identity = get_identity(size=54)

        # Test that move applied twice equals double move
        test_symbols = ["U", "R", "F", "x", "y"]
        for raw_symbol in test_symbols:
            move_symbol = MoveSymbol(raw_symbol)
            double_move_symbol = MoveSymbol(raw_symbol + "2")
            if double_move_symbol in permutations:
                # Apply move twice
                result = identity[permutations[move_symbol]][permutations[move_symbol]]
                expected = identity[permutations[double_move_symbol]]
                assert np.array_equal(result, expected)

    def test_caching(self) -> None:
        # Test that repeated calls return the same object (cached)
        permutations1 = create_permutations(cube_size=3)
        permutations2 = create_permutations(cube_size=3)
        assert permutations1 is permutations2


class TestPermutationProperties:
    """Test algebraic properties of permutations."""

    def test_permutation_composition_associative(self) -> None:
        identity = get_identity(size=54)
        permutations = create_permutations(cube_size=3)

        # Test associativity
        a = permutations[MoveSymbol("U")]
        b = permutations[MoveSymbol("R")]
        c = permutations[MoveSymbol("F")]

        ab = identity[a][b]
        abc1 = ab[c]

        bc = identity[b][c]
        abc2 = identity[a][bc]

        assert np.array_equal(abc1, abc2)

    def test_identity_is_identity(self) -> None:
        identity = get_identity(size=54)
        permutations = create_permutations(cube_size=3)

        # Test I * A == A * I == A for any move A
        for move_symbol, move_permutation in permutations.items():
            # I * A
            ia = identity[permutations[MoveSymbol("I")]][move_permutation]
            # A * I
            ai = identity[move_permutation][permutations[MoveSymbol("I")]]

            assert np.array_equal(ia, identity[move_permutation]), (
                f"I * {move_symbol} != {move_symbol}"
            )
            assert np.array_equal(ai, identity[move_permutation]), (
                f"{move_symbol} * I != {move_symbol}"
            )

    def test_move_orders(self) -> None:
        identity = get_identity(size=54)
        permutations = create_permutations(cube_size=3)

        # Test that U^4 = I (quarter turn has order 4)
        result = identity
        for _ in range(4):
            result = result[permutations[MoveSymbol("U")]]
        assert np.array_equal(result, identity)

        # Test that U2^2 = I (half turn has order 2)
        result = identity[permutations[MoveSymbol("U2")]][permutations[MoveSymbol("U2")]]
        assert np.array_equal(result, identity)

    def test_rotation_orders(self) -> None:
        identity = get_identity(size=54)
        permutations = create_permutations(cube_size=3)

        # Test that x^4 = I (rotation has order 4)
        x = MoveSymbol("x")
        result = identity
        for _ in range(4):
            result = result[permutations[x]]
        assert np.array_equal(result, identity)


class TestEdgeCases:
    def test_different_cube_sizes(self) -> None:
        for cube_size in [1, 2, 3, 4, 5]:
            get_identity(size=6 * cube_size**2)
            permutations = create_permutations(cube_size=cube_size)

            # Test that all permutations have correct size
            expected_size = 6 * cube_size**2
            for permutation in permutations.values():
                assert len(permutation) == expected_size
                assert is_permutation(permutation)
