from enum import Enum


class Face(Enum):
    Up = "U"
    Front = "F"
    Right = "R"
    Blue = "B"
    Left = "L"
    Down = "D"
    Empty = "G"


class Metric(Enum):
    HTM = "HTM"
    STM = "STM"
    QTM = "QTM"


COLORS = {
    Face.Up.value: "#FFFFFF",
    Face.Front.value: "#00d800",
    Face.Right.value: "#e00000",
    Face.Blue.value: "#1450f0",
    Face.Left.value: "#ff7200",
    Face.Down.value: "#ffff00",
    Face.Empty.value: "#606060",
}
