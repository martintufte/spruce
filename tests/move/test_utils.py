from __future__ import annotations

import pytest

from rubiks_cube.move.utils import strip_move
from rubiks_cube.move.utils import unstrip_move


class TestDecorateMove:
    @pytest.mark.parametrize(
        "move",
        [
            ("R"),
            ("(R"),
            ("R)"),
            ("(R)"),
        ],
    )
    def test_strip_move(self, move: str) -> None:
        """Test that decorated moves are stripped correctly."""
        assert strip_move(move) == "R"

    @pytest.mark.parametrize(
        "move",
        [
            ("R"),
            ("(R"),
            ("R)"),
            ("(R)"),
        ],
    )
    def test_unstrip_move(self, move: str) -> None:
        """Test that decorated moves are decorated correctly."""
        assert unstrip_move(move) == "(R)"
