import re

import pytest

from rubiks_cube.formatting.regex import MOVE_REGEX


class TestMoveRegex:
    @pytest.mark.parametrize(
        "move",
        [
            (""),
            ("I"),
            ("Lw"),
            ("Lw2"),
            ("Lw'"),
        ],
    )
    def test_move_regex(self, move: str) -> None:
        """Test that the move regex matches valid moves."""
        assert bool(re.match(MOVE_REGEX, move))

    @pytest.mark.parametrize(
        "move",
        [
            ("L2'"),
            ("Lw3"),
            ("2Lw"),
        ],
    )
    def test_move_regex_fail(self, move: str) -> None:
        """Test that the move regex does not matches invalid moves."""
        assert not bool(re.match(MOVE_REGEX, move))
