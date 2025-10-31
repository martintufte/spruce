from __future__ import annotations

import numpy as np

from rubiks_cube.configuration import DEFAULT_GENERATOR
from rubiks_cube.move.generator import MoveGenerator
from rubiks_cube.move.scrambler import scramble_generator
from rubiks_cube.move.sequence import MoveSequence


def test_scramble_generator_2x2() -> None:
    """Test that scramble generator can generate scrambles for 2x2 cubes."""
    generator = MoveGenerator("<R, U, F>")
    length = 10
    cube_size = 2
    n_scrambles = 5

    scrambles = list(scramble_generator(length, generator, cube_size, n_scrambles))

    assert len(scrambles) == n_scrambles
    for scramble in scrambles:
        assert isinstance(scramble, MoveSequence)
        assert len(scramble) == length
        valid_moves = {"R", "R'", "R2", "U", "U'", "U2", "F", "F'", "F2"}
        for move in scramble.moves:
            assert move in valid_moves


def test_scramble_generator_4x4() -> None:
    """Test that scramble generator can generate scrambles for 4x4 cubes."""
    generator = MoveGenerator("<R, U, F, Rw>")
    length = 15
    cube_size = 4
    n_scrambles = 3

    scrambles = list(scramble_generator(length, generator, cube_size, n_scrambles))

    assert len(scrambles) == n_scrambles
    for scramble in scrambles:
        assert isinstance(scramble, MoveSequence)
        assert len(scramble) == length
        valid_moves = {"R", "R'", "R2", "U", "U'", "U2", "F", "F'", "F2", "Rw", "Rw'", "Rw2"}
        for move in scramble.moves:
            assert move in valid_moves


def test_scramble_generator_reproducible_rng() -> None:
    """Test that scramble generator produces reproducible results with fixed RNG seed."""
    generator = MoveGenerator(DEFAULT_GENERATOR)
    length = 8
    cube_size = 3
    n_scrambles = 3
    seed = 42

    # Generate scrambles with fixed seed
    rng1 = np.random.default_rng(seed)
    scrambles1 = list(scramble_generator(length, generator, cube_size, n_scrambles, rng1))

    # Generate scrambles again with same seed
    rng2 = np.random.default_rng(seed)
    scrambles2 = list(scramble_generator(length, generator, cube_size, n_scrambles, rng2))

    # Results should be identical
    assert len(scrambles1) == len(scrambles2)
    for scramble1, scramble2 in zip(scrambles1, scrambles2, strict=False):
        assert scramble1.moves == scramble2.moves
        assert str(scramble1) == str(scramble2)

    # Test that different seeds produce different results
    rng3 = np.random.default_rng(123)
    scrambles3 = list(scramble_generator(length, generator, cube_size, n_scrambles, rng3))

    # At least one scramble should be different (very high probability)
    different = any(s1.moves != s3.moves for s1, s3 in zip(scrambles1, scrambles3, strict=False))
    assert different, "Different seeds should produce different scrambles"
