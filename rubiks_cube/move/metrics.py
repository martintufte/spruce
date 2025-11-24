from __future__ import annotations

import re
from typing import Sequence

from rubiks_cube.configuration import DEFAULT_METRIC
from rubiks_cube.configuration.enumeration import Metric
from rubiks_cube.formatting.regex import DOUBLE_ROTATION_SEARCH
from rubiks_cube.formatting.regex import DOUBLE_SEARCH
from rubiks_cube.formatting.regex import DOUBLE_SLICE_SEARCH
from rubiks_cube.formatting.regex import IDENTITY_SEARCH
from rubiks_cube.formatting.regex import ROTATION_SEARCH
from rubiks_cube.formatting.regex import SLICE_SEARCH


def measure_moves(moves: Sequence[str], metric: Metric = DEFAULT_METRIC) -> int:
    """Count the length of a sequence of moves.

    Args:
        moves (Sequence[str]): Sequence of moves.
        metric (Metric, optional): Metric type. Defaults to DEFAULT_METRIC.

    Returns:
        int: Length of the sequence.
    """
    count = sum(not bool(re.search(IDENTITY_SEARCH, move)) for move in moves)

    if metric is Metric.ETM:
        return count

    slices = sum(bool(re.search(SLICE_SEARCH, move)) for move in moves)
    rotations = sum(bool(re.search(ROTATION_SEARCH, move)) for move in moves)

    if metric is Metric.HTM:
        return count + slices - rotations

    if metric is Metric.STM:
        return count - rotations

    if metric is Metric.QTM:
        d_count = sum(bool(re.search(DOUBLE_SEARCH, move)) for move in moves)
        d_slices = sum(bool(re.search(DOUBLE_SLICE_SEARCH, move)) for move in moves)
        d_rotations = sum(bool(re.search(DOUBLE_ROTATION_SEARCH, move)) for move in moves)
        return count + slices - rotations + d_count + d_slices - d_rotations


def quarter_turn_parity(moves: Sequence[str]) -> bool:
    """Find the quarter turn parity of a sequence of moves.

    Args:
        moves (Sequence[str]): List of moves.

    Returns:
        bool: Parity of the sequence. True if even, False if odd.
    """
    return bool(measure_moves(moves, Metric.QTM) % 2)
