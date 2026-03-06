from __future__ import annotations

import numpy as np

from rubiks_cube.move.meta import MoveMeta
from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.move.sequence import cancel_moves


def test_from_cube_size_is_cached() -> None:
    MoveMeta.from_cube_size.cache_clear()
    meta_first = MoveMeta.from_cube_size(3)
    meta_second = MoveMeta.from_cube_size(3)

    assert meta_first is meta_second


def test_basic_sets() -> None:
    meta = MoveMeta.from_cube_size(3)

    assert "I" not in meta.legal_moves
    assert "x" in meta.rotation_moves
    assert "y" in meta.rotation_moves
    assert "z" in meta.rotation_moves
    assert "x" not in meta.legal_moves
    assert "R" in meta.legal_moves


def test_compose_contains_basic_cancellations() -> None:
    meta = MoveMeta.from_cube_size(3)

    assert meta.compose[("R", "R")] == "R2"
    assert meta.compose[("R", "R'")] == ""
    assert meta.compose[("U'", "U")] == ""


def test_commutation_examples() -> None:
    meta = MoveMeta.from_cube_size(3)

    assert "L" in meta.commutes["R"]
    assert "R" in meta.commutes["L"]
    assert "U" not in meta.commutes["R"]


def test_compose_matches_permutation_product() -> None:
    meta = MoveMeta.from_cube_size(3)
    for move_a, move_b in [("R", "R"), ("U", "U2"), ("F", "F'")]:
        combined = meta.compose[(move_a, move_b)]
        perm_combined = meta.permutations[move_a][meta.permutations[move_b]]
        if combined == "":
            assert np.array_equal(perm_combined, meta.permutations["I"])
        else:
            assert np.array_equal(perm_combined, meta.permutations[combined])


def test_cancel_moves() -> None:
    base = "L F Rw2 Rw2 F' L Rw L' R Rw "
    seq = MoveSequence.from_str(base) * 199
    move_meta = MoveMeta.from_cube_size(3)

    cancel_moves(seq, move_meta)

    assert seq == MoveSequence.from_str("Lw' Rw")


class TestHasParity:
    move_meta_2x2 = MoveMeta.from_cube_size(2)
    move_meta_3x3 = MoveMeta.from_cube_size(3)

    def test_2x2_has_parity(self) -> None:
        assert self.move_meta_2x2.has_parity

    def test_3x3_not_has_parity(self) -> None:
        assert not self.move_meta_3x3.has_parity
