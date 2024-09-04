from typing import Final

from rubiks_cube.utils.enums import Face
from rubiks_cube.utils.enums import Metric

CUBE_SIZE: Final = 3
METRIC: Final = Metric.HTM

COLOR_SCHEME: Final[dict[Face, str]] = {
    Face.up: "#FFFFFF",
    Face.front: "#00d800",
    Face.right: "#e00000",
    Face.back: "#1450f0",
    Face.left: "#ff7200",
    Face.down: "#ffff00",
    Face.no_face: "#606060",
}
