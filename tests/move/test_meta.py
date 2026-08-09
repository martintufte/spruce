from __future__ import annotations

import numpy as np

from spruce.configuration.enumeration import Puzzle
from spruce.move.meta import MoveMeta
from spruce.move.sequence import MoveSequence
from spruce.types import MoveSymbol
from spruce.types import PermutationClassification


class TestMoveMeta:
    puzzle = Puzzle._3x3x3

    def test_from_cube_size_is_cached(self) -> None:
        MoveMeta.from_puzzle.cache_clear()
        meta_first = MoveMeta.from_puzzle(puzzle=self.puzzle)
        meta_second = MoveMeta.from_puzzle(puzzle=self.puzzle)

        assert meta_first is meta_second

    def test_grouping(self) -> None:
        meta = MoveMeta.from_puzzle(puzzle=self.puzzle)

        assert "I" not in meta.base_moves
        assert "x" in meta.rotation_moves
        assert "y" in meta.rotation_moves
        assert "z" in meta.rotation_moves
        assert "x" not in meta.base_moves
        assert "R" in meta.base_moves
        assert "Rw" in meta.base_moves
        assert "M" in meta.base_moves

    def test_compose_contains_basic_cancellations(self) -> None:
        meta = MoveMeta.from_puzzle(puzzle=self.puzzle)

        assert meta.compose[(MoveSymbol("R"), MoveSymbol("R"))] == "R2"
        assert meta.compose[(MoveSymbol("R"), MoveSymbol("R'"))] == ""
        assert meta.compose[(MoveSymbol("U'"), MoveSymbol("U"))] == ""

    def test_commutation_examples(self) -> None:
        meta = MoveMeta.from_puzzle(puzzle=self.puzzle)

        assert "L" in meta.commutes[MoveSymbol("R")]
        assert "R" in meta.commutes[MoveSymbol("L")]
        assert "U" not in meta.commutes[MoveSymbol("R")]

    def test_compose_matches_permutation_product(self) -> None:
        meta = MoveMeta.from_puzzle(puzzle=self.puzzle)
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
        meta = MoveMeta.from_puzzle(puzzle=self.puzzle)
        assert len(meta.pieces) == 20
        corners = [piece for piece in meta.pieces if len(piece) == 3]
        edges = [piece for piece in meta.pieces if len(piece) == 2]
        assert len(corners) == 8
        assert len(edges) == 12

    def test_reduce(self) -> None:
        base = "L F Rw2 Rw2 F' L Rw L' R Rw "
        seq = MoveSequence.from_str(base) * 199
        move_meta = MoveMeta.from_puzzle(puzzle=self.puzzle)

        seq.normal = move_meta.reduce(seq.normal)

        assert seq == MoveSequence.from_str("Lw' Rw")

    def test_2x2_has_parity(self) -> None:
        meta = MoveMeta.from_puzzle(Puzzle._2x2x2)
        assert meta.has_parity

    def test_3x3_not_has_parity(self) -> None:
        meta = MoveMeta.from_puzzle(puzzle=self.puzzle)
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
            puzzle=Puzzle._2x2x2,
        )

        assert move_meta.size == 4
        assert len(move_meta.pieces) == 4
        assert move_meta.has_parity

        # Test invert a word:
        word = [MoveSymbol("a"), MoveSymbol("c"), MoveSymbol("b")]
        expected = [MoveSymbol("b"), MoveSymbol("c"), MoveSymbol("a")]

        inverted_word = move_meta.invert(word)
        assert inverted_word == expected
