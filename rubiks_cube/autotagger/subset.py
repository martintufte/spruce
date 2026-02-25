from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from typing import Literal

import numpy as np

from rubiks_cube.configuration.enumeration import Piece
from rubiks_cube.representation.mask import get_piece_mask
from rubiks_cube.representation.permutation import create_permutations
from rubiks_cube.representation.utils import invert

if TYPE_CHECKING:
    from rubiks_cube.configuration.types import CubePermutation

LOGGER = logging.getLogger(__name__)


HTR_PATTERN = np.array([1] * 9 + ([2] * 9 + [3] * 9) * 2 + [1] * 9)
CORNER_GROUPS = {
    "UBL": (0, 29, 36),
    "UFL": (6, 9, 38),
    "UBR": (2, 20, 27),
    "UFR": (8, 11, 18),
    "DBL": (35, 42, 51),
    "DFL": (15, 44, 45),
    "DBR": (26, 33, 53),
    "DFR": (17, 24, 47),
}
CORNER_BY_FACE = {
    "U": ("UBL", "UFL", "UBR", "UFR"),
    "D": ("DBL", "DFL", "DBR", "DFR"),
    "F": ("UFL", "UFR", "DFL", "DFR"),
    "B": ("UBL", "UBR", "DBL", "DBR"),
    "L": ("UBL", "UFL", "DBL", "DFL"),
    "R": ("UBR", "UFR", "DBR", "DFR"),
}


def _corner_is_bad(permutation: CubePermutation, corner_name: str) -> bool:
    idxs = CORNER_GROUPS[corner_name]
    idxs_arr = np.array(idxs)
    return any(HTR_PATTERN[permutation[idxs_arr]] != HTR_PATTERN[idxs_arr])


def _count_bad_corners_in_face(permutation: CubePermutation, face: str) -> int:
    return sum(_corner_is_bad(permutation, name) for name in CORNER_BY_FACE[face])


def _mental_swap_to_real_htr(permutation: CubePermutation, corner_names: list[str]) -> bool:
    if len(corner_names) != 2:
        LOGGER.warning(f"Expected two bad corners for mental swapping, got {corner_names}")

    swapped = np.copy(permutation)
    first_idxs = CORNER_GROUPS[corner_names[0]]
    second_idxs = CORNER_GROUPS[corner_names[1]]
    swapped[[*first_idxs, *second_idxs]] = permutation[[*second_idxs, *first_idxs]]

    return distinguish_htr(swapped) == "real"


def _has_one_three_split(permutation: CubePermutation, axis_faces: tuple[str, str]) -> bool:
    face_a, face_b = axis_faces
    count_a = _count_bad_corners_in_face(permutation, face_a)
    count_b = _count_bad_corners_in_face(permutation, face_b)
    return min(count_a, count_b) == 1


def corner_trace(permutation: CubePermutation) -> str:
    """Return the corner cycles.

    Args:
        permutation (CubePermutation): Cube permutation.

    Returns:
        str: Corner cycles.
    """
    # Define the corners and their idxs
    # TODO: The corner positions here are hardcoded!
    corners = {
        "UBL": [0, 29, 36],
        "UFL": [6, 9, 38],
        "UBR": [2, 20, 27],
        "UFR": [8, 11, 18],
        "DBL": [35, 42, 51],
        "DFL": [15, 44, 45],
        "DBR": [26, 33, 53],
        "DFR": [17, 24, 47],
    }

    # Keep track of explored corners and cycles
    explored_corners = set()
    cycles = []

    # Loop over all corners
    for corner_idxs in corners.values():
        current_corner_idxs = corner_idxs.copy()

        cycle = 0
        while current_corner_idxs[0] not in explored_corners:
            explored_corners.update(current_corner_idxs)
            current_corner_idxs = list(permutation[current_corner_idxs])
            cycle += 1

        if cycle > 1:
            cycles.append(cycle)

    return "".join([f"{n}c" for n in sorted(cycles, reverse=True)])


def edge_trace(permutation: CubePermutation) -> str:
    """Return the edge cycles.

    Args:
        permutation (CubePermutation): Permutation.

    Returns:
        str: Edge cycles.
    """
    # Define the edges and their idxs
    edges = {
        "UB": [1, 28],
        "UL": [3, 37],
        "UR": [5, 19],
        "UF": [7, 10],
        "BL": [32, 39],
        "FL": [12, 41],
        "BR": [23, 30],
        "FR": [21, 14],
        "DB": [34, 52],
        "DL": [43, 48],
        "DR": [25, 50],
        "DF": [16, 46],
    }

    # Keep track of explored edges and cycles
    explored_edges = set()
    cycles = []

    # Loop over all edges
    for edge_idxs in edges.values():
        current_edge_idxs = edge_idxs.copy()

        cycle = 0
        while current_edge_idxs[0] not in explored_edges:
            explored_edges.update(current_edge_idxs)
            cycle += 1
            current_edge_idxs = list(permutation[current_edge_idxs])

        if cycle > 1:
            cycles.append(cycle)

    return "".join([f"{n}e" for n in sorted(cycles, reverse=True)])


# TODO: This works, but should be replaced with a non-stochastic method!
# If uses on average ~2 moves to differentiate between real/fake HTR
# It recognizes if it is real/fake HTR by corner-tracing
def distinguish_htr(permutation: CubePermutation) -> Literal["fake", "real"]:
    """Distinguish between real and fake HTR patterns.

    Args:
        permutation (CubePermutation): Cube permutation.

    Returns:
        Literal["fake", "real"]: Real or fake HTR.
    """
    assert permutation.size == 54, "Only 3x3 cubes are supported."

    real_htr_traces = ["", "2c2c2c2c"]
    fake_htr_traces = [
        "3c2c2c",
        "2c2c2c",
        "4c3c",
        "4c",
        "2c",
        "3c2c",
        "4c2c2c",
        "3c",
    ]
    # real/fake = ["3c3c", "4c2c", "2c2c", "4c4c"]

    rng = np.random.default_rng(seed=42)
    permutations = create_permutations(cube_size=3)
    current_permutation = np.copy(permutation)

    subset = "htr-like"

    while subset == "htr-like":
        trace = corner_trace(current_permutation)
        if trace in real_htr_traces:
            subset = "real"
        elif trace in fake_htr_traces:
            subset = "fake"
        else:
            move = rng.choice(["R2", "U2", "F2"], size=1)[0]
            current_permutation = current_permutation[permutations[move]]

    return subset


# TODO: This works, but should be replaced with a more permanent solution
# as it is a very human-like approach to distinguish DR subsets
def get_dr_subset_label(tag: str, permutation: CubePermutation) -> str:
    """Return the DR subset for a permutation.

    Format: "XcX Xe" - Number of bad corners, bad edges and quarter turns.

    Args:
        permutation (CubePermutation): Cube permutation.

    Returns:
        str: Domino reduction subset label.
    """
    # Determine the number of good and bad edges
    mismatch_mask = HTR_PATTERN[permutation] != HTR_PATTERN
    bad_corners = np.count_nonzero(mismatch_mask[get_piece_mask(Piece.corner, cube_size=3)]) // 2
    bad_edges = np.count_nonzero(mismatch_mask[get_piece_mask(Piece.edge, cube_size=3)])
    letter = "c"

    # Determine the quarter turn parity using blind trace
    # Add up the amount of corners in each cycle minus 1, then mod 2
    def is_parity(permutation: CubePermutation) -> bool:
        trace = corner_trace(permutation)
        qt_parity_count = 0
        for n in trace.split("c"):
            if n:
                qt_parity_count += int(n) - 1
        return qt_parity_count % 2 == 1

    permutations = create_permutations(cube_size=3)
    current_permutation = np.copy(permutation)

    # Simplify so bad corners is reduced to [0, 2, 4]
    if bad_corners in [6, 8]:
        if tag == "dr-ud":
            current_permutation = current_permutation[permutations["U"]]
            current_permutation = current_permutation[permutations["D"]]
        elif tag == "dr-lr":
            current_permutation = current_permutation[permutations["L"]]
            current_permutation = current_permutation[permutations["R"]]
        elif tag == "dr-fb":
            current_permutation = current_permutation[permutations["F"]]
            current_permutation = current_permutation[permutations["B"]]

    # 0/8 bad corners: QT = 0 (real htr) or 3 (parity) else 4
    if bad_corners in [0, 8]:
        # Distinguish real/fake htr:
        if distinguish_htr(current_permutation) == "real":
            qt = "0"
        elif is_parity(current_permutation):
            qt = "3"
        else:
            qt = "4"

    # 2/6 bad corners: QT = 4 (not parity) or 5 (mental swap to real htr) else 3
    elif bad_corners in [2, 6]:
        if not is_parity(current_permutation):
            qt = "4"
        else:
            bad_corner_names = [
                name for name in CORNER_GROUPS if _corner_is_bad(current_permutation, name)
            ]
            qt = "5" if _mental_swap_to_real_htr(current_permutation, bad_corner_names) else "3"

    # 4 bad corners: QT = 2 (even, a/a or b/b) or 4 (even, a/b or b/a)
    # or 1 (odd, a/a) or 3 (odd, a/b or b/a) or 5 (odd, b/b)
    else:
        axis_pairs = (("U", "D"), ("L", "R"), ("F", "B"))
        is_2qt_lookalike = any(
            _has_one_three_split(current_permutation, pair) for pair in axis_pairs
        )
        is_2qt_lookalike_inv = any(
            _has_one_three_split(invert(current_permutation), pair) for pair in axis_pairs
        )
        parity = is_parity(current_permutation)
        if parity:
            if not is_2qt_lookalike and not is_2qt_lookalike_inv:
                qt = "1"
                letter = "a"
            elif is_2qt_lookalike and is_2qt_lookalike_inv:
                qt = "5"
            else:
                qt = "3"
        elif is_2qt_lookalike == is_2qt_lookalike_inv:
            qt = 2
            letter = "b" if is_2qt_lookalike else "a"
        else:
            qt = 4

    return f"{bad_corners}{letter}{qt} {bad_edges}e"
