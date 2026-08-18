from __future__ import annotations

from enum import Enum
from enum import unique


@unique
class Puzzle(Enum):
    _1x1x1 = "1x1x1"
    _2x2x2 = "2x2x2"
    _3x3x3 = "3x3x3"
    _4x4x4 = "4x4x4"
    _5x5x5 = "5x5x5"
    _6x6x6 = "6x6x6"
    _7x7x7 = "7x7x7"
    _8x8x8 = "8x8x8"
    _9x9x9 = "9x9x9"

    @property
    def cube_size(self) -> int:
        return int(self.value[0])
