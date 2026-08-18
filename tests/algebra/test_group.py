from __future__ import annotations

import numpy as np
import pytest

from spruce.algebra.group import MoveMeta
from spruce.algebra.group import PermutationClassification
from spruce.move.sequence import MoveSequence
from spruce.puzzle.cube.group import build_move_meta
from spruce.puzzle.cube.spec import Puzzle
from spruce.types import MoveSymbol


class TestMoveMeta:
    puzzle = Puzzle._3x3x3

    def test_grouping(self) -> None:
        meta = build_move_meta(puzzle=self.puzzle)

        assert "I" not in meta.base_symbols
        assert "x" in meta.rotation_symbols
        assert "y" in meta.rotation_symbols
        assert "z" in meta.rotation_symbols
        assert "x" not in meta.base_symbols
        assert "R" in meta.base_symbols
        assert "Rw" in meta.base_symbols
        assert "M" in meta.base_symbols

    def test_compose_contains_basic_cancellations(self) -> None:
        meta = build_move_meta(puzzle=self.puzzle)

        assert meta.compose[(MoveSymbol("R"), MoveSymbol("R"))] == "R2"
        assert meta.compose[(MoveSymbol("R"), MoveSymbol("R'"))] == ""
        assert meta.compose[(MoveSymbol("U'"), MoveSymbol("U"))] == ""

    def test_commutation_examples(self) -> None:
        meta = build_move_meta(puzzle=self.puzzle)

        assert "L" in meta.commutes[MoveSymbol("R")]
        assert "R" in meta.commutes[MoveSymbol("L")]
        assert "U" not in meta.commutes[MoveSymbol("R")]

    def test_compose_matches_permutation_product(self) -> None:
        meta = build_move_meta(puzzle=self.puzzle)
        pairs = [("R", "R"), ("U", "U2"), ("F", "F'")]
        for symbol_a, symbol_b in pairs:
            move_a, move_b = MoveSymbol(symbol_a), MoveSymbol(symbol_b)
            combined = meta.compose[(move_a, move_b)]
            perm_combined = meta.permutations[move_a][meta.permutations[move_b]]
            if combined == "":
                assert np.array_equal(perm_combined, meta.permutations[MoveSymbol("I")])
            else:
                assert np.array_equal(perm_combined, meta.permutations[combined])

    def test_pieces(self) -> None:
        meta = build_move_meta(puzzle=self.puzzle)
        assert len(meta.pieces) == 20
        corners = [piece for piece in meta.pieces if len(piece) == 3]
        edges = [piece for piece in meta.pieces if len(piece) == 2]
        assert len(corners) == 8
        assert len(edges) == 12

    def test_reduce(self) -> None:
        base = "L F Rw2 Rw2 F' L Rw L' R Rw "
        seq = MoveSequence.from_str(base) * 199
        move_meta = build_move_meta(puzzle=self.puzzle)

        seq.normal = move_meta.reduce(seq.normal)

        assert seq == MoveSequence.from_str("Lw' Rw")

    def test_2x2_has_parity(self) -> None:
        meta = build_move_meta(Puzzle._2x2x2)
        assert meta.has_parity

    def test_3x3_not_has_parity(self) -> None:
        meta = build_move_meta(puzzle=self.puzzle)
        assert not meta.has_parity

    def test_from_permutation(self) -> None:
        permutations = {
            MoveSymbol("i"): np.array([0, 1, 2, 3]),
            MoveSymbol("a"): np.array([1, 0, 2, 3]),
            MoveSymbol("b"): np.array([0, 2, 1, 3]),
            MoveSymbol("c"): np.array([0, 1, 3, 2]),
        }

        classifications = {
            MoveSymbol("i"): PermutationClassification.IDENTITY,
            MoveSymbol("a"): PermutationClassification.BASE,
            MoveSymbol("b"): PermutationClassification.BASE,
            MoveSymbol("c"): PermutationClassification.BASE,
        }

        move_meta = MoveMeta.from_permutations(
            permutations=permutations,
            classifications=classifications,
            name="test group",
        )

        assert move_meta.size == 4
        assert len(move_meta.pieces) == 4
        assert move_meta.has_parity

        # Test invert a word:
        word = [MoveSymbol("a"), MoveSymbol("c"), MoveSymbol("b")]
        expected = [MoveSymbol("b"), MoveSymbol("c"), MoveSymbol("a")]

        inverted_word = move_meta.invert(word)
        assert inverted_word == expected


class TestSymbolValidation:
    """Every string entering the system as a `MoveSymbol` must pass through here."""

    move_meta: MoveMeta = build_move_meta(puzzle=Puzzle._3x3x3)

    # Syntactically valid notation, but not a move of a 3x3x3
    wrong_puzzle_symbol = "3Rw"
    junk_symbol = "banana"

    def test_symbols_contains_every_permutation_key(self) -> None:
        """Test that the symbol collection is exactly the keys of the permutations."""
        assert self.move_meta.symbols == frozenset(self.move_meta.permutations)
        assert (
            self.move_meta.base_symbols | self.move_meta.rotation_symbols <= self.move_meta.symbols
        )

    def test_to_symbols_accepts_known_symbols(self) -> None:
        assert self.move_meta.to_symbols("R", "U2", "M'") == frozenset({"R", "U2", "M'"})

    def test_to_symbols_rejects_symbol_of_another_puzzle(self) -> None:
        """Test that well formed notation is still rejected when the puzzle lacks it."""
        assert self.wrong_puzzle_symbol not in self.move_meta.symbols

        with pytest.raises(ValueError, match=r"Unknown move symbols \['3Rw'\]"):
            self.move_meta.to_symbols("R", self.wrong_puzzle_symbol)

    def test_to_symbols_rejects_junk(self) -> None:
        with pytest.raises(ValueError, match=r"Unknown move symbols \['banana'\]"):
            self.move_meta.to_symbols(self.junk_symbol)

    def test_to_word_keeps_order_and_repeats(self) -> None:
        """Test that a word is ordered, unlike the set returned by `to_symbols`."""
        assert self.move_meta.to_word(["U", "R", "U"]) == ["U", "R", "U"]
        assert self.move_meta.to_symbols("U", "R", "U") == frozenset({"U", "R"})

    def test_to_word_rejects_unknown_symbol(self) -> None:
        with pytest.raises(ValueError, match=r"Unknown move symbols \['banana'\]"):
            self.move_meta.to_word(["R", self.junk_symbol])
