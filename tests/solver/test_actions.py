from __future__ import annotations

from typing import TYPE_CHECKING

from spruce.configuration import DEFAULT_GENERATOR_MAP
from spruce.move.generator import MoveGenerator
from spruce.move.meta import MoveMeta
from spruce.solver.actions import get_actions

if TYPE_CHECKING:
    from spruce.move.sequence import MoveSequence


class TestGetActions:
    move_meta: MoveMeta = MoveMeta.from_cube_size(3)

    def test_get_actions_empty_set(self) -> None:
        """Test get actions from empty set."""
        sequence_set: set[MoveSequence] = set()
        generator = MoveGenerator(sequence_set)
        actions = get_actions(move_meta=self.move_meta, generator=generator)
        assert len(actions) == 0

    def test_get_actions_empty_generator(self) -> None:
        """Test get empty move sequence results in identity."""
        generator = MoveGenerator.from_str("<>")
        actions = get_actions(move_meta=self.move_meta, generator=generator)
        assert len(actions) == 1

    def test_get_actions_standard_moves(self) -> None:
        """Test get standard moves actions."""
        generator = MoveGenerator.from_str(DEFAULT_GENERATOR_MAP[3])
        actions = get_actions(move_meta=self.move_meta, generator=generator, expand=False)
        assert len(actions) == 6

        actions_expanded = get_actions(move_meta=self.move_meta, generator=generator)
        assert len(actions_expanded) == 18

    def test_get_actions_right(self) -> None:
        """Test get standard moves actions with no expanding."""
        generator = MoveGenerator.from_str("<R>")
        actions = get_actions(move_meta=self.move_meta, generator=generator)
        assert len(actions) == 3

    def test_get_actions_right_double(self) -> None:
        """Test get standard moves actions with no expanding."""
        generator = MoveGenerator.from_str("<R2>")
        actions = get_actions(move_meta=self.move_meta, generator=generator)
        assert len(actions) == 1

    def test_get_actions_duplicate(self) -> None:
        """Test get actions from duplicate sequences."""
        generator = MoveGenerator.from_str("<R, R, R>")
        actions = get_actions(move_meta=self.move_meta, generator=generator, expand=False)
        assert len(actions) == 1
