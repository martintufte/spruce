from __future__ import annotations

import numpy as np

from spruce.move.scrambler import scramble_generator
from spruce.move.sequence import MoveSequence
from spruce.puzzle.cube.group import build_move_meta
from spruce.puzzle.cube.spec import Puzzle


def test_scramble_generator_2x2() -> None:
    """Test that scramble generator can generate scrambles for 2x2 cubes."""
    move_meta = build_move_meta(puzzle=Puzzle._2x2x2)
    generator = move_meta.to_symbols("R", "U", "F")
    length = 10
    n_scrambles = 5

    scrambles = list(scramble_generator(length, generator, move_meta, n_scrambles))

    assert len(scrambles) == n_scrambles
    for scramble in scrambles:
        assert isinstance(scramble, MoveSequence)
        assert len(scramble) == length
        assert not scramble.inverse
        valid_symbols = {"R", "R'", "R2", "U", "U'", "U2", "F", "F'", "F2"}
        for symbol in scramble.normal:
            assert symbol in valid_symbols


def test_scramble_generator_4x4() -> None:
    """Test that scramble generator can generate scrambles for 4x4 cubes."""
    move_meta = build_move_meta(puzzle=Puzzle._4x4x4)
    generator = move_meta.to_symbols("R", "U", "F", "Rw")
    length = 15
    n_scrambles = 3

    scrambles = list(scramble_generator(length, generator, move_meta, n_scrambles))

    assert len(scrambles) == n_scrambles
    for scramble in scrambles:
        assert isinstance(scramble, MoveSequence)
        assert len(scramble) == length
        assert not scramble.inverse
        valid_symbols = {"R", "R'", "R2", "U", "U'", "U2", "F", "F'", "F2", "Rw", "Rw'", "Rw2"}
        for symbol in scramble.normal:
            assert symbol in valid_symbols


def test_scramble_generator_reproducible_rng() -> None:
    """Test that scramble generator produces reproducible results with fixed RNG seed."""
    puzzle = Puzzle._3x3x3
    move_meta = build_move_meta(puzzle=puzzle)
    generator = move_meta.default_generator
    length = 8
    n_scrambles = 3
    seed = 42

    # Generate scrambles with fixed seed
    rng1 = np.random.default_rng(seed)
    scrambles1 = list(scramble_generator(length, generator, move_meta, n_scrambles, rng1))

    # Generate scrambles again with same seed
    rng2 = np.random.default_rng(seed)
    scrambles2 = list(scramble_generator(length, generator, move_meta, n_scrambles, rng2))

    # Results should be identical
    assert len(scrambles1) == len(scrambles2)
    for scramble1, scramble2 in zip(scrambles1, scrambles2, strict=False):
        assert scramble1.normal == scramble2.normal
        assert str(scramble1) == str(scramble2)

    # Test that different seeds produce different results
    rng3 = np.random.default_rng(123)
    scrambles3 = list(scramble_generator(length, generator, move_meta, n_scrambles, rng3))

    # At least one scramble should be different (very high probability)
    different = any(s1.normal != s3.normal for s1, s3 in zip(scrambles1, scrambles3, strict=False))
    assert different, "Different seeds should produce different scrambles"
