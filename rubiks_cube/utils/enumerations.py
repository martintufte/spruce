from enum import Enum


class Face(Enum):
    up = "U"
    front = "F"
    right = "R"
    blue = "B"
    left = "L"
    down = "D"
    empty = "G"


class Metric(Enum):
    HTM = "HTM"
    STM = "STM"
    QTM = "QTM"
    ETM = "ETM"


class Piece(Enum):
    corner = "corner"
    edge = "edge"
    center = "center"
