from typing import Final

from rubiks_cube.configuration.enumeration import Face
from rubiks_cube.configuration.enumeration import Metric

CUBE_SIZE: Final = 3
METRIC: Final = Metric.HTM

COLOR_SCHEME: Final[dict[Face, str]] = {
    Face.up: "white",
    Face.front: "green",
    Face.right: "red",
    Face.back: "blue",
    Face.left: "orange",
    Face.down: "yellow",
    Face.empty: "gray",
}
