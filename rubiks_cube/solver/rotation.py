from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import numpy as np

from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.representation import get_rubiks_cube_state

if TYPE_CHECKING:
    from rubiks_cube.configuration.types import CubeMask
    from rubiks_cube.configuration.types import CubePermutation


LOGGER = logging.getLogger(__name__)


# TODO: Reimplement
def find_rotation_offset(
    permutation: CubePermutation,
    affected_mask: CubeMask | None,
    cube_size: int,
) -> CubePermutation | None:
    """Find the rotational offset between the permutation and the mask.

    It finds the rotation such that permutation[~affected_mask] == identity[~affected_mask].

    Args:
        permutation (CubePermutation): Initial permutation.
        affected_mask (CubeMask | None, optional): Mask of what is affected by the actions.
        cube_size (int): Size of the cube.

    Returns:
        CubePermutation | None: Rotation offset for the permutation.

    Raises:
        ValueError: could not infer cube size.
    """

    # Assume everything is affected if not provided
    if affected_mask is None:
        affected_mask = np.ones_like(permutation, dtype=bool)

    not_affected_mask = ~affected_mask

    # Naming: XY, X is the up face, Y is the front face
    standard_rotations = {
        "UF": [],
        "UL": ["y'"],
        "UB": ["y2"],
        "UR": ["y"],
        "FU": ["x", "y2"],
        "FL": ["x", "y'"],
        "FD": ["x"],
        "FR": ["x", "y"],
        "RU": ["z'", "y'"],
        "RF": ["z'"],
        "RD": ["z'", "y"],
        "RB": ["z'", "y2"],
        "BU": ["x'"],
        "BL": ["x'", "y'"],
        "BD": ["x'", "y2"],
        "BR": ["x'", "y"],
        "LU": ["z", "y"],
        "LF": ["z"],
        "LD": ["z", "y'"],
        "LB": ["z", "y2"],
        "DF": ["z2"],
        "DL": ["x2", "y'"],
        "DB": ["x2"],
        "DR": ["x2", "y"],
    }

    for rotation_sequence in standard_rotations.values():
        rotation = get_rubiks_cube_state(
            sequence=MoveSequence(rotation_sequence),
            cube_size=cube_size,
        )
        if np.array_equal(rotation[not_affected_mask], permutation[not_affected_mask]):
            return rotation

    return None
