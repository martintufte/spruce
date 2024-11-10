import pytest

from rubiks_cube.formatting.string import format_string
from rubiks_cube.formatting.string import format_whitespaces
from rubiks_cube.formatting.string import is_valid_symbols
from rubiks_cube.formatting.string import remove_redundant_parenteses
from rubiks_cube.formatting.string import replace_confusing_chars
from rubiks_cube.formatting.string import replace_move_rotation
from rubiks_cube.formatting.string import replace_wide_notation
from rubiks_cube.formatting.string import strip_comments
from rubiks_cube.formatting.string import try_balance_parenteses


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
        raw_text = "R U R’ U’"
        replaced_text = replace_confusing_chars(raw_text)
        assert replaced_text == "R U R' U'"


class TestIsValidSymbols:
    def test_valid_symbols(self) -> None:
        raw_text = "(f\txR 2 (U2'  M')L 3D w2()\n F2 ( Bw ' y ' F'))"
        assert is_valid_symbols(raw_text)

    def test_valid_symbols_additional(self) -> None:
        raw_text = "(f\txR 2 ([U2'  M'])L 3D w2()\n F2 ( Bw ' y ' F'))"
        assert is_valid_symbols(raw_text, additional_chars="[]")

    def test_valid_symbols_no_additional(self) -> None:
        raw_text = "(f\txR 2 ([U2'  M'])L 3D w2()\n F2 ( Bw ' y ' F'))"
        assert not is_valid_symbols(raw_text)


class TestFormatParenteses:
    def test_remove_redundant_parenteses_end_start(self) -> None:
        raw_text = "(R U) (R' U')"
        formatted_text = remove_redundant_parenteses(raw_text)
        assert formatted_text == "(R U R' U')"

    def test_remove_redundant_parenteses_empty_parenteses(self) -> None:
        raw_text = "R U R' U'()"
        formatted_text = remove_redundant_parenteses(raw_text)
        assert formatted_text == "R U R' U'"

    def test_remove_redundant_parenteses_unbalanced_start(self) -> None:
        raw_text = "(R U R' U'"
        with pytest.raises(ValueError):
            try_balance_parenteses(raw_text)

    def test_remove_redundant_parenteses_unbalanced_stacked(self) -> None:
        raw_text = "(R U (R' (U'))"
        with pytest.raises(ValueError):
            try_balance_parenteses(raw_text)

    def test_remove_redundant_parenteses_unbalanced_end(self) -> None:
        raw_text = "R (U R') U')"
        with pytest.raises(ValueError):
            try_balance_parenteses(raw_text)


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
