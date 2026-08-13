import pytest

from spruce.move.formatting import format_string
from spruce.move.formatting import format_whitespaces
from spruce.move.formatting import has_valid_characters
from spruce.move.formatting import remove_redundant_parentheses
from spruce.move.formatting import replace_confusing_chars
from spruce.move.formatting import replace_move_rotation
from spruce.move.formatting import replace_wide_notation
from spruce.move.formatting import strip_comments
from spruce.move.formatting import strip_move
from spruce.move.formatting import try_balance_parentheses


class TestStripComments:
    def test_strip_no_comments(self) -> None:
        raw_text = "R U R' U'  "
        stripped_text = strip_comments(raw_text)
        assert stripped_text == "R U R' U'"

    def test_strip_comments_no_space(self) -> None:
        raw_text = "R U R' U'//Comment"
        stripped_text = strip_comments(raw_text)
        assert stripped_text == "R U R' U'"

    def test_strip_comments(self) -> None:
        raw_text = "R U R' U'  // Comment"
        stripped_text = strip_comments(raw_text)
        assert stripped_text == "R U R' U'"

    def test_strip_double_comments(self) -> None:
        raw_text = "R U R' U'  // Comment  // Second comment"
        stripped_text = strip_comments(raw_text)
        assert stripped_text == "R U R' U'"

    def test_strip_comments_penta(self) -> None:
        raw_text = "R U R' U'  ///// Comment"
        stripped_text = strip_comments(raw_text)
        assert stripped_text == "R U R' U'"


class TestReplaceConfusingCharacters:
    def test_replace_confusing_characters(self) -> None:
        raw_text = "R U R’ U’"  # noqa: RUF001
        replaced_text = replace_confusing_chars(raw_text)
        assert replaced_text == "R U R' U'"


class TestIsValidSymbols:
    def test_valid_symbols(self) -> None:
        raw_text = "(f\txR 2 (U2'  M')L 3D w2()\n F2 ( Bw ' y ' F'))"
        assert has_valid_characters(raw_text)

    def test_valid_symbols_additional(self) -> None:
        raw_text = "(f\txR 2 ([U2'  M'])L 3D w2()\n F2 ( Bw ' y ' F'))"
        assert has_valid_characters(raw_text, additional_chars="[]")

    def test_valid_symbols_no_additional(self) -> None:
        raw_text = "(f\txR 2 ([U2'  M'])L 3D w2()\n F2 ( Bw ' y ' F'))"
        assert not has_valid_characters(raw_text)


class TestFormatParentheses:
    def test_remove_redundant_parentheses_end_start(self) -> None:
        raw_text = "(R U) (R' U')"
        formatted_text = remove_redundant_parentheses(raw_text)
        assert formatted_text == "(R U R' U')"

    def test_remove_redundant_parentheses_empty_parentheses(self) -> None:
        raw_text = "R U R' U'()"
        formatted_text = remove_redundant_parentheses(raw_text)
        assert formatted_text.strip() == "R U R' U'"

    def test_remove_redundant_parentheses_unbalanced_start(self) -> None:
        raw_text = "(R U R' U'"
        with pytest.raises(ValueError, match="Unbalanced parentheses!"):
            try_balance_parentheses(raw_text)

    def test_remove_redundant_parentheses_unbalanced_stacked(self) -> None:
        raw_text = "(R U (R' (U'))"
        with pytest.raises(ValueError, match="Unbalanced parentheses!"):
            try_balance_parentheses(raw_text)

    def test_remove_redundant_parentheses_unbalanced_end(self) -> None:
        raw_text = "R (U R') U')"
        with pytest.raises(ValueError, match="Unbalanced parentheses!"):
            try_balance_parentheses(raw_text)


class TestFormatWhitespace:
    def test_format_whitespace_all_space(self) -> None:
        raw_text = " ( f \t x R 2 ( U 2 ' M ' ) \n L 3 D w 2 ( ) F 2 ( B w ' y ' F ' ) ) "
        formatted_string = format_whitespaces(raw_text)
        assert formatted_string == "(f x R2 (U2' M') L 3Dw2 () F2 (Bw' y' F'))"

    def test_format_whitespace_no_space(self) -> None:
        raw_text = "(fxR2(U2'M')L3Dw2()F2(Bw'y'F'))"
        formatted_string = format_whitespaces(raw_text)
        assert formatted_string == "(f x R2 (U2' M') L 3Dw2 () F2 (Bw' y' F'))"

    def test_format_whitespace_already_formatted(self) -> None:
        raw_text = "(f x R2 (U2' M') L 3Dw2 () F2 (Bw' y' F'))"
        formatted_string = format_whitespaces(raw_text)
        assert formatted_string == "(f x R2 (U2' M') L 3Dw2 () F2 (Bw' y' F'))"

    def test_wide_edge_cases(self) -> None:
        raw_text = "Rw3Fw"
        formatted_string = format_whitespaces(raw_text)
        assert formatted_string == "Rw 3Fw"

        raw_text = "Rw2Fw"
        formatted_string = format_whitespaces(raw_text)
        assert formatted_string == "Rw2 Fw"


class TestFormatMoveRotation:
    def test_format_move_rotation(self) -> None:
        raw_text = "R2' (3Dw2')"
        formatted_string = replace_move_rotation(raw_text)
        assert formatted_string == "R2 (3Dw2)"


class TestFormatWideNotation:
    def test_format_wide_notation(self) -> None:
        raw_text = "r2 (3f')"
        formatted_string = replace_wide_notation(raw_text)
        assert formatted_string == "Rw2 (3Fw')"


class TestFormatString:
    def test_format_string(self) -> None:
        raw_text = "(f\txR 2 (U2'  M')L 3D w2()\n F2 ( Bw ' y ' F'))"
        formatted_string = format_string(raw_text)
        assert formatted_string == "(Fw x R2) U2 M' (L 3Dw2 F2) Bw' y' F'"


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
