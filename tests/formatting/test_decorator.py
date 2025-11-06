import pytest

from rubiks_cube.formatting.decorator import decorate_move
from rubiks_cube.formatting.decorator import strip_move
from rubiks_cube.formatting.decorator import undecorate_move


class TestDecorateMove:
    @pytest.mark.parametrize(
        "move",
        [
            ("R"),
            ("(R)"),
        ],
    )
    def test_strip_move(self, move: str) -> None:
        """Test that decorated moves are stripped correctly."""
        assert strip_move(move) == "R"

    @pytest.mark.parametrize(
        "move, niss, expected",
        [
            ("R", False, "R"),
            ("R", True, "(R)"),
        ],
    )
    def test_decorate_move(self, move: str, niss: bool, expected: str) -> None:
        """Test that decorated moves are decorated correctly."""
        assert decorate_move(move, niss) == expected

    @pytest.mark.parametrize(
        "move",
        [
            ("R"),
            ("(R)"),
        ],
    )
    def test_decorate_move_roundtrip(self, move: str) -> None:
        """Test that decorated moves are decorated correctly."""
        undecorated_move, niss = undecorate_move(move)
        assert decorate_move(undecorated_move, niss) == move
