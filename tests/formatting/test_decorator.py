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
            ("~R~"),
            ("(~R~)"),
        ],
    )
    def test_strip_move(self, move: str) -> None:
        """Test that decorated moves are stripped correctly."""
        assert strip_move(move) == "R"

    @pytest.mark.parametrize(
        "move, niss, slash, expected",
        [
            ("R", False, False, "R"),
            ("R", True, False, "(R)"),
            ("R", False, True, "~R~"),
            ("R", True, True, "(~R~)"),
        ],
    )
    def test_decorate_move(self, move: str, niss: bool, slash: bool, expected: str) -> None:
        """Test that decorated moves are decorated correctly."""
        assert decorate_move(move, niss, slash) == expected

    @pytest.mark.parametrize(
        "move",
        [
            ("R"),
            ("(R)"),
            ("~R~"),
            ("(~R~)"),
        ],
    )
    def test_decorate_move_roundtrip(self, move: str) -> None:
        """Test that decorated moves are decorated correctly."""
        undecorated_move, niss, slash = undecorate_move(move)
        assert decorate_move(undecorated_move, niss, slash) == move
