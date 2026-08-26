from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from spruce.puzzle.cube.group import build_move_meta
from spruce.puzzle.cube.group import default_generator
from spruce.puzzle.cube.notation import parse_moves
from spruce.puzzle.cube.notation import parse_sequence
from spruce.puzzle.cube.spec import Puzzle

if TYPE_CHECKING:
    from spruce.algebra.meta import MoveMeta


class TestBuildMoveMeta:
    puzzle = Puzzle._3x3x3
    move_meta: MoveMeta = build_move_meta(puzzle=Puzzle._3x3x3)

    # Syntactically valid notation, but not a move of a 3x3x3
    wrong_puzzle_symbol = "3Rw"

    def test_build_move_meta_is_cached(self) -> None:
        build_move_meta.cache_clear()
        meta_first = build_move_meta(puzzle=self.puzzle)
        meta_second = build_move_meta(puzzle=self.puzzle)

        assert meta_first is meta_second

    def test_to_sequence_parses_both_sides(self) -> None:
        sequence = parse_sequence(move_meta=self.move_meta, string="R U (F')")

        assert sequence.normal == ["R", "U"]
        assert sequence.inverse == ["F'"]

    def test_to_sequence_rejects_symbol_of_another_puzzle(self) -> None:
        """Test that `to_sequence` checks the puzzle, which `from_str` does not."""
        assert parse_moves(self.wrong_puzzle_symbol).normal == [self.wrong_puzzle_symbol]

        with pytest.raises(ValueError, match=r"Unknown move symbols \['3Rw'\]"):
            parse_sequence(move_meta=self.move_meta, string=f"R {self.wrong_puzzle_symbol} U")

    def test_to_sequence_checks_the_inverse_side(self) -> None:
        with pytest.raises(ValueError, match=r"Unknown move symbols \['3Rw'\]"):
            parse_sequence(move_meta=self.move_meta, string=f"R ({self.wrong_puzzle_symbol})")

    def test_default_generator_is_validated(self) -> None:
        assert default_generator(self.puzzle) == frozenset({"U", "D", "L", "R", "F", "B"})
        assert default_generator(self.puzzle) <= self.move_meta.symbols

    def test_default_generator_differs_per_puzzle(self) -> None:
        assert default_generator(Puzzle._2x2x2) == frozenset({"U", "R", "F"})
        assert "Rw" in default_generator(Puzzle._4x4x4)

    def test_default_generator_rejects_puzzle_without_one(self) -> None:
        with pytest.raises(ValueError, match="No default generator defined"):
            default_generator(Puzzle._5x5x5)
