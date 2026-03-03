import pytest

from rubiks_cube.configuration.enumeration import Metric
from rubiks_cube.move.metrics import measure_moves


@pytest.mark.parametrize(
    "moves, expected_ETH, expected_HTM, expected_STM, expected_QTM",
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
def test_measure_moves(
    moves: list[str],
    expected_ETH: int,
    expected_HTM: int,
    expected_STM: int,
    expected_QTM: int,
) -> None:
    assert measure_moves(moves, Metric.ETM) == expected_ETH
    assert measure_moves(moves, Metric.HTM) == expected_HTM
    assert measure_moves(moves, Metric.STM) == expected_STM
    assert measure_moves(moves, Metric.QTM) == expected_QTM
