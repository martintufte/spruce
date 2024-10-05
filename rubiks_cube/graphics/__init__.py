import numpy as np

from rubiks_cube.configuration import CUBE_SIZE
from rubiks_cube.configuration.enumeration import Face
from rubiks_cube.configuration.type_definitions import CubeState


def get_colored_rubiks_cube(
    state: CubeState | None = None,
    as_int: bool = False,
    cube_size: int = CUBE_SIZE,
) -> CubeState:
    """Get a cube state with its colors.

    Args:
        state (CubeState | None, optional): State of the cube. Defaults to None.
        as_int (bool, optional): Whether to return the representation as int. Defaults to False.
        cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.

    Returns:
        CubeState: Cube state with colors.
    """

    face_dict = {
        0: Face.up,
        1: Face.front,
        2: Face.right,
        3: Face.back,
        4: Face.left,
        5: Face.down,
    }
    colored_cube = np.arange(6 * cube_size**2, dtype=int) // cube_size**2

    if state is not None:
        assert state.size == 6 * cube_size**2, "Invalid state length!"
        colored_cube = colored_cube[state]
    if as_int:
        return colored_cube

    return np.array([face_dict[color] for color in colored_cube], dtype=Face)
