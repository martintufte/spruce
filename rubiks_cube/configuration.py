from typing import Final

from rubiks_cube.utils.enumerations import AttemptType
from rubiks_cube.utils.enumerations import Face
from rubiks_cube.utils.enumerations import Metric
from rubiks_cube.utils.enumerations import Pattern

# Constants for the application
CUBE_SIZE: Final = 4
METRIC: Final = Metric.HTM
ATTEMPT_TYPE: Final = AttemptType.fewest_moves

COLOR_SCHEME = {
    Face.up: "#FFFFFF",
    Face.front: "#00d800",
    Face.right: "#e00000",
    Face.back: "#1450f0",
    Face.left: "#ff7200",
    Face.down: "#ffff00",
    Pattern.empty: "#606060",
    Pattern.mask: "#90ee90",
    Pattern.relative_mask: "#658ba7",
    Pattern.orientation: "#c2b280",
}
