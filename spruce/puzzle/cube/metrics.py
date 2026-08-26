from __future__ import annotations

import re
from enum import Enum
from enum import unique
from functools import lru_cache
from typing import TYPE_CHECKING

from spruce.puzzle.cube.notation import DOUBLE_ROTATION_SEARCH
from spruce.puzzle.cube.notation import DOUBLE_SEARCH
from spruce.puzzle.cube.notation import DOUBLE_SLICE_SEARCH
from spruce.puzzle.cube.notation import IDENTITY_SEARCH
from spruce.puzzle.cube.notation import ROTATION_SEARCH
from spruce.puzzle.cube.notation import SLICE_SEARCH

if TYPE_CHECKING:
    from collections.abc import Sequence

    from spruce.algebra.sequence import MoveSequence
    from spruce.types import MoveSymbol


@unique
class Metric(Enum):
    ETM = "Execution Turn Metric"
    HTM = "Half Turn Metric"
    STM = "Slice Turn Metric"
    QTM = "Quarter Turn Metric"


@lru_cache(maxsize=4096)
def _symbol_cost(symbol: MoveSymbol, metric: Metric) -> int:
    """Cost of a single symbol under the metric.

    Every term of a metric is a count of symbols matching some pattern, combined with
    fixed integer coefficients, so the cost of a word is the sum of its symbols' costs.
    Caching this keeps the notation matching off the hot path.
    """
    turn = 0 if re.search(IDENTITY_SEARCH, symbol) else 1

    if metric is Metric.ETM:
        return turn

    is_slice = bool(re.search(SLICE_SEARCH, symbol))
    is_rotation = bool(re.search(ROTATION_SEARCH, symbol))

    if metric is Metric.HTM:
        return turn + is_slice - is_rotation

    if metric is Metric.STM:
        return turn - is_rotation

    if metric is Metric.QTM:
        is_double = bool(re.search(DOUBLE_SEARCH, symbol))
        is_double_slice = bool(re.search(DOUBLE_SLICE_SEARCH, symbol))
        is_double_rotation = bool(re.search(DOUBLE_ROTATION_SEARCH, symbol))
        return turn + is_slice - is_rotation + is_double + is_double_slice - is_double_rotation

    raise ValueError(f"No symbol cost defined for metric {metric}")


def _measure_word(word: Sequence[MoveSymbol], metric: Metric) -> int:
    """Count the length of a word under the metric."""
    return sum(_symbol_cost(symbol, metric) for symbol in word)


def measure(sequence: MoveSequence, metric: Metric) -> int:
    """Measure the length of a move sequence using the metric."""
    return _measure_word(sequence.normal, metric) + _measure_word(sequence.inverse, metric)
