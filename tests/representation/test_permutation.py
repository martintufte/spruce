import numpy as np
import pytest

from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.representation.permutation import apply_moves_to_permutation
from rubiks_cube.representation.permutation import create_permutations
from rubiks_cube.representation.permutation import get_identity_permutation
from rubiks_cube.representation.permutation import get_permutation_dictionary
from tests.conftest import is_permutation


class TestGetIdentityPermutation:
    """Test get_identity_permutation function."""

    def test_identity_3x3(self) -> None:
        identity = get_identity_permutation(cube_size=3)
        expected = np.arange(54)
        assert np.array_equal(identity, expected)
        assert is_permutation(identity)

    def test_identity_2x2(self) -> None:
        identity = get_identity_permutation(cube_size=2)
        expected = np.arange(24)
        assert np.array_equal(identity, expected)
        assert is_permutation(identity)

    def test_identity_4x4(self) -> None:
        identity = get_identity_permutation(cube_size=4)
        expected = np.arange(96)
        assert np.array_equal(identity, expected)
        assert is_permutation(identity)

    def test_identity_1x1(self) -> None:
        identity = get_identity_permutation(cube_size=1)
        expected = np.arange(6)
        assert np.array_equal(identity, expected)
        assert is_permutation(identity)

    def test_invalid_cube_sizes(self) -> None:
        with pytest.raises(AssertionError):
            get_identity_permutation(cube_size=0)
        with pytest.raises(AssertionError):
            get_identity_permutation(cube_size=11)
        with pytest.raises(AssertionError):
            get_identity_permutation(cube_size=-1)


class TestCreatePermutations:
    """Test create_permutations function."""

    def test_create_permutations_3x3(self) -> None:
        perms = create_permutations(cube_size=3)
        identity = get_identity_permutation(cube_size=3)

        # Test identity
        assert np.array_equal(perms["I"], identity)

        # Test all permutations are valid
        for move, perm in perms.items():
            assert is_permutation(perm), f"Move {move} is not a valid permutation"
            assert len(perm) == 54, f"Move {move} has wrong length"

    def test_create_permutations_2x2(self) -> None:
        perms = create_permutations(cube_size=2)
        identity = get_identity_permutation(cube_size=2)

        # Test identity
        assert np.array_equal(perms["I"], identity)

        # Test all permutations are valid
        for move, perm in perms.items():
            assert is_permutation(perm), f"Move {move} is not a valid permutation"
            assert len(perm) == 24, f"Move {move} has wrong length"

    def test_basic_moves_present(self) -> None:
        perms = create_permutations(cube_size=3)

        # Test basic face moves are present
        basic_moves = [
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
        for move in basic_moves:
            assert move in perms, f"Move {move} not found in permutations"

        # Test rotations are present
        rotations = ["x", "x'", "x2", "y", "y'", "y2", "z", "z'", "z2"]
        for rotation in rotations:
            assert rotation in perms, f"Rotation {rotation} not found in permutations"

    def test_slice_moves_3x3(self) -> None:
        perms = create_permutations(cube_size=3)

        # Test slice moves for 3x3
        slice_moves = ["M", "M'", "M2", "E", "E'", "E2", "S", "S'", "S2"]
        for move in slice_moves:
            assert move in perms, f"Slice move {move} not found in 3x3 permutations"

    def test_no_slice_moves_2x2(self) -> None:
        perms = create_permutations(cube_size=2)

        # Test slice moves are not present for 2x2
        slice_moves = ["M", "M'", "M2", "E", "E'", "E2", "S", "S'", "S2"]
        for move in slice_moves:
            assert move not in perms, f"Slice move {move} should not be in 2x2 permutations"

    def test_wide_moves(self) -> None:
        perms = create_permutations(cube_size=3)

        # Test wide moves are present
        wide_moves = ["Uw", "Uw'", "Uw2", "Rw", "Rw'", "Rw2"]
        for move in wide_moves:
            assert move in perms, f"Wide move {move} not found in permutations"

    def test_move_inverses(self) -> None:
        perms = create_permutations(cube_size=3)
        identity = get_identity_permutation(cube_size=3)

        # Test that move and its inverse compose to identity
        test_moves = ["U", "R", "F", "x", "y"]
        for move in test_moves:
            move_inv = move + "'"
            if move_inv in perms:
                # Apply move then its inverse
                result = identity[perms[move]][perms[move_inv]]
                assert np.array_equal(
                    result, identity
                ), f"{move} and {move_inv} don't compose to identity"

    def test_move_doubles(self) -> None:
        perms = create_permutations(cube_size=3)
        identity = get_identity_permutation(cube_size=3)

        # Test that move applied twice equals double move
        test_moves = ["U", "R", "F", "x", "y"]
        for move in test_moves:
            move_double = move + "2"
            if move_double in perms:
                # Apply move twice
                result = identity[perms[move]][perms[move]]
                expected = identity[perms[move_double]]
                assert np.array_equal(result, expected), f"{move} applied twice != {move_double}"

    def test_caching(self) -> None:
        # Test that repeated calls return the same object (cached)
        perms1 = create_permutations(cube_size=3)
        perms2 = create_permutations(cube_size=3)
        assert perms1 is perms2, "create_permutations should return cached result"


class TestGetPermutationDictionary:
    """Test get_permutation_dictionary function."""

    def test_get_permutation_dictionary_basic(self) -> None:
        identity = get_identity_permutation(cube_size=3)
        # Create simple test rotations
        x = np.roll(identity, 1)  # Simple test transformation
        y = np.roll(identity, 2)  # Simple test transformation
        us = [np.roll(identity, 3)]  # Simple test U move

        perms = get_permutation_dictionary(identity, x, y, us, cube_size=3)

        # Test basic structure
        assert "I" in perms
        assert "x" in perms
        assert "y" in perms
        assert "U" in perms
        assert np.array_equal(perms["I"], identity)


class TestApplyMovesToPermutation:
    """Test apply_moves_to_permutation function."""

    def test_apply_empty_sequence(self) -> None:
        identity = get_identity_permutation(cube_size=3)
        sequence = MoveSequence("")
        result = apply_moves_to_permutation(identity, sequence, cube_size=3)
        assert np.array_equal(result, identity)

    def test_apply_single_move(self) -> None:
        identity = get_identity_permutation(cube_size=3)
        perms = create_permutations(cube_size=3)
        sequence = MoveSequence("U")

        result = apply_moves_to_permutation(identity, sequence, cube_size=3)
        expected = identity[perms["U"]]
        assert np.array_equal(result, expected)

    def test_apply_multiple_moves(self) -> None:
        identity = get_identity_permutation(cube_size=3)
        perms = create_permutations(cube_size=3)
        sequence = MoveSequence("U R")

        result = apply_moves_to_permutation(identity, sequence, cube_size=3)
        expected = identity[perms["U"]][perms["R"]]
        assert np.array_equal(result, expected)

    def test_apply_move_and_inverse(self) -> None:
        identity = get_identity_permutation(cube_size=3)
        sequence = MoveSequence("U U'")

        result = apply_moves_to_permutation(identity, sequence, cube_size=3)
        assert np.array_equal(result, identity)

    def test_apply_move_four_times(self) -> None:
        identity = get_identity_permutation(cube_size=3)
        sequence = MoveSequence("U U U U")

        result = apply_moves_to_permutation(identity, sequence, cube_size=3)
        assert np.array_equal(result, identity)

    def test_result_is_valid_permutation(self) -> None:
        identity = get_identity_permutation(cube_size=3)
        sequence = MoveSequence("R U R' U' R' F R2 U' R' U' R U R' F'")

        result = apply_moves_to_permutation(identity, sequence, cube_size=3)
        assert is_permutation(result)


class TestPermutationProperties:
    """Test mathematical properties of permutations."""

    def test_permutation_composition_associative(self) -> None:
        identity = get_identity_permutation(cube_size=3)
        perms = create_permutations(cube_size=3)

        # Test (A * B) * C == A * (B * C)
        a, b, c = perms["U"], perms["R"], perms["F"]

        # (A * B) * C
        ab = identity[a][b]
        abc1 = ab[c]

        # A * (B * C)
        bc = identity[b][c]
        abc2 = identity[a][bc]

        assert np.array_equal(abc1, abc2)

    def test_identity_is_identity(self) -> None:
        identity = get_identity_permutation(cube_size=3)
        perms = create_permutations(cube_size=3)

        # Test I * A == A * I == A for any move A
        for move_name, move_perm in list(perms.items())[:10]:  # Test subset
            # I * A
            ia = identity[perms["I"]][move_perm]
            # A * I
            ai = identity[move_perm][perms["I"]]

            assert np.array_equal(ia, identity[move_perm]), f"I * {move_name} != {move_name}"
            assert np.array_equal(ai, identity[move_perm]), f"{move_name} * I != {move_name}"

    def test_move_orders(self) -> None:
        identity = get_identity_permutation(cube_size=3)
        perms = create_permutations(cube_size=3)

        # Test that U^4 = I (quarter turn has order 4)
        result = identity
        for _ in range(4):
            result = result[perms["U"]]
        assert np.array_equal(result, identity)

        # Test that U2^2 = I (half turn has order 2)
        result = identity[perms["U2"]][perms["U2"]]
        assert np.array_equal(result, identity)

    def test_rotation_orders(self) -> None:
        identity = get_identity_permutation(cube_size=3)
        perms = create_permutations(cube_size=3)

        # Test that x^4 = I (rotation has order 4)
        result = identity
        for _ in range(4):
            result = result[perms["x"]]
        assert np.array_equal(result, identity)


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_different_cube_sizes(self) -> None:
        for cube_size in [1, 2, 3, 4, 5]:
            identity = get_identity_permutation(cube_size=cube_size)
            perms = create_permutations(cube_size=cube_size)

            # Test that all permutations have correct size
            expected_size = 6 * cube_size**2
            for move, perm in perms.items():
                assert (
                    len(perm) == expected_size
                ), f"Move {move} has wrong size for {cube_size}x{cube_size}"
                assert is_permutation(perm), f"Move {move} is invalid for {cube_size}x{cube_size}"

    def test_invalid_move_sequence(self) -> None:
        identity = get_identity_permutation(cube_size=3)
        # This should raise ValueError for invalid move string
        with pytest.raises(ValueError):
            apply_moves_to_permutation(identity, MoveSequence("X"), cube_size=3)
