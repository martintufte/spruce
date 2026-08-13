from __future__ import annotations

import re
from typing import TYPE_CHECKING

from spruce.configuration.enumeration import Metric
from spruce.configuration.regex import DOUBLE_ROTATION_SEARCH
from spruce.configuration.regex import DOUBLE_SEARCH
from spruce.configuration.regex import DOUBLE_SLICE_SEARCH
from spruce.configuration.regex import IDENTITY_SEARCH
from spruce.configuration.regex import ROTATION_SEARCH
from spruce.configuration.regex import SLICE_SEARCH

if TYPE_CHECKING:
    from collections.abc import Sequence

    from spruce.types import MoveSymbol


# TODO(martin): Move the measurement to MoveMeta
def measure_word(word: Sequence[MoveSymbol], metric: Metric) -> int:
    """Count the length of a word.

    Args:
        word (Sequence[MoveSymbol]): Word; sequence of symbols.
        metric (Metric): Metric type.

    Returns:
        int: Length of the word.
    """
    count = sum(not bool(re.search(IDENTITY_SEARCH, symbol)) for symbol in word)

    if metric is Metric.ETM:
        return count

    slices = sum(bool(re.search(SLICE_SEARCH, symbol)) for symbol in word)
    rotations = sum(bool(re.search(ROTATION_SEARCH, symbol)) for symbol in word)

    if metric is Metric.HTM:
        return count + slices - rotations

    if metric is Metric.STM:
        return count - rotations

    if metric is Metric.QTM:
        d_count = sum(bool(re.search(DOUBLE_SEARCH, symbol)) for symbol in word)
        d_slices = sum(bool(re.search(DOUBLE_SLICE_SEARCH, symbol)) for symbol in word)
        d_rotations = sum(bool(re.search(DOUBLE_ROTATION_SEARCH, symbol)) for symbol in word)
        return count + slices - rotations + d_count + d_slices - d_rotations
