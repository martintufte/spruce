from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from spruce.configuration.enumeration import Metric
from spruce.move.metrics import measure_word

if TYPE_CHECKING:
    from spruce.types import MoveSymbol


@pytest.mark.parametrize(
    ("word", "expected_eth", "expected_htm", "expected_stm", "expected_qtm"),
    [
        # Empty move
        ([], 0, 0, 0, 0),
        # Identity moves
        (["I"], 0, 0, 0, 0),
        (["i"], 0, 0, 0, 0),
        # Rotations
        (["x"], 1, 0, 0, 0),
        (["x'"], 1, 0, 0, 0),
        (["x2"], 1, 0, 0, 0),
        # Single move
        (["R"], 1, 1, 1, 1),
        (["R'"], 1, 1, 1, 1),
        (["R2"], 1, 1, 1, 2),
        # Wide moves
        (["Rw"], 1, 1, 1, 1),
        (["Rw'"], 1, 1, 1, 1),
        (["Rw2"], 1, 1, 1, 2),
        # Trippel wide moves
        (["3Rw"], 1, 1, 1, 1),
        (["3Rw'"], 1, 1, 1, 1),
        (["3Rw2"], 1, 1, 1, 2),
        # Middle slice
        (["M"], 1, 2, 1, 2),
        (["M'"], 1, 2, 1, 2),
        (["M2"], 1, 2, 1, 4),
    ],
)
def test_measure_word(
    word: list[MoveSymbol],
    expected_eth: int,
    expected_htm: int,
    expected_stm: int,
    expected_qtm: int,
) -> None:
    assert measure_word(word, Metric.ETM) == expected_eth
    assert measure_word(word, Metric.HTM) == expected_htm
    assert measure_word(word, Metric.STM) == expected_stm
    assert measure_word(word, Metric.QTM) == expected_qtm
