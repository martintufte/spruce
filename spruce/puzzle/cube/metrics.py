from __future__ import annotations

from enum import Enum
from enum import unique


@unique
class Metric(Enum):
    ETM = "Execution Turn Metric"
    HTM = "Half Turn Metric"
    STM = "Slice Turn Metric"
    QTM = "Quarter Turn Metric"
