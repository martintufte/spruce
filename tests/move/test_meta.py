from __future__ import annotations

from rubiks_cube.move.meta import MoveMeta
from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.move.sequence import cancel_moves


def test_cancel_moves() -> None:
    base = "L F Rw2 Rw2 F' L Rw L' R Rw "
    seq = MoveSequence.from_str(base) * 199

    move_meta = MoveMeta.from_cube_size(3)

    cancel_moves(seq, move_meta)

    assert seq == MoveSequence.from_str("Lw' Rw")
