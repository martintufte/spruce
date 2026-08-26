from __future__ import annotations

import numpy as np

from spruce.algebra import get_permutation
from spruce.algebra.sequence import MoveSequence
from spruce.puzzle.cube.group import build_move_meta
from spruce.puzzle.cube.notation import parse_moves
from spruce.puzzle.cube.spec import Puzzle


class TestGetPermutationAliasing:
    def test_empty_sequence_returns_fresh_array(self) -> None:
        move_meta = build_move_meta(puzzle=Puzzle._3x3x3)
        initial = np.arange(move_meta.size, dtype=np.uint)

        result = get_permutation(
            sequence=MoveSequence(),
            move_meta=move_meta,
            initial_permutation=initial,
        )

        assert np.array_equal(result, initial)
        assert result is not initial
        result[0] = 42
        assert initial[0] == 0

    def test_initial_permutation_is_not_mutated(self) -> None:
        move_meta = build_move_meta(puzzle=Puzzle._3x3x3)
        initial = np.arange(move_meta.size, dtype=np.uint)
        initial_copy = initial.copy()

        get_permutation(
            sequence=parse_moves("R U R' U' (F R2)"),
            move_meta=move_meta,
            initial_permutation=initial,
        )

        assert np.array_equal(initial, initial_copy)

    def test_orientate_after_does_not_mutate_sequence(self) -> None:
        move_meta = build_move_meta(puzzle=Puzzle._3x3x3)
        sequence = parse_moves("R x U M (F y2 R2)")
        normal_before = list(sequence.normal)
        inverse_before = list(sequence.inverse)

        get_permutation(
            sequence=sequence,
            move_meta=move_meta,
            orientate_after=True,
        )

        assert sequence.normal == normal_before
        assert sequence.inverse == inverse_before
