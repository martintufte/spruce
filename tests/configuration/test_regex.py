import re

import pytest

from rubiks_cube.configuration.regex import MOVE_REGEX


class TestMoveRegex:
    @pytest.mark.parametrize(
        "move",
        [
            ("I"),
            (""),
            ("L"),
            ("L'"),
            ("L2"),
            ("Lw"),
            ("Lw'"),
            ("Lw2"),
            ("3Lw"),
            ("3Lw'"),
            ("3Lw2"),
            ("9Lw"),
            ("9Lw'"),
            ("9Lw2"),
            ("x"),
            ("x'"),
            ("x2"),
            ("M"),
            ("M'"),
            ("M2"),
        ],
    )
    def test_move_regex(self, move: str) -> None:
        """Test that the move regex matches valid moves."""
        assert bool(re.match(MOVE_REGEX, move))

    @pytest.mark.parametrize(
        "move",
        [
            (" "),
            ("2"),
            ("'"),
            ("l"),
            (" L"),
            ("L "),
            ("LL"),
            ("2L"),
            ("L2'"),
            ("Lw3"),
            ("2Lw"),
            ("10Lw"),
            ("wL"),
            ("(L)"),
            ("~L~"),
        ],
    )
    def test_move_regex_fail(self, move: str) -> None:
        """Test that the move regex does not matches invalid moves."""
        assert not bool(re.match(MOVE_REGEX, move))
