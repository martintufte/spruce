from __future__ import annotations

from enum import Enum
from enum import unique


@unique
class Piece(Enum):
    center = "center"
    corner = "corner"
    edge = "edge"
