from __future__ import annotations

import pytest

from spruce.configuration import DEFAULT_GENERATOR_MAP
from spruce.configuration.enumeration import Puzzle
from spruce.move.meta import MoveMeta
from spruce.types import move_symbols


class TestGetActions:
    move_meta: MoveMeta = MoveMeta.from_puzzle(puzzle=Puzzle._3x3x3)

    def test_get_actions_empty_generator(self) -> None:
        """Test get actions from an empty set of symbols."""
        actions = self.move_meta.get_actions(generator=set())
        assert len(actions) == 0

    def test_get_actions_standard_moves(self) -> None:
        """Test get standard moves actions."""
        puzzle = Puzzle._3x3x3
        generator = DEFAULT_GENERATOR_MAP[puzzle]
        actions = self.move_meta.get_actions(generator=generator, expand=False)
        assert len(actions) == 6

        actions_expanded = self.move_meta.get_actions(generator=generator)
        assert len(actions_expanded) == 18

    def test_get_actions_right(self) -> None:
        """Test that a single symbol expands to its powers."""
        actions = self.move_meta.get_actions(generator=move_symbols("R"))
        assert len(actions) == 3

    def test_get_actions_right_double(self) -> None:
        """Test that a self-inverse symbol does not expand."""
        actions = self.move_meta.get_actions(generator=move_symbols("R2"))
        assert len(actions) == 1

    def test_get_actions_unknown_symbol(self) -> None:
        """Test that a symbol not contained in the move meta raises."""
        with pytest.raises(ValueError, match="Unknown move symbol"):
            self.move_meta.get_actions(generator=move_symbols("R U R'"))
