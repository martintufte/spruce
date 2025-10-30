from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from rubiks_cube.representation.permutation import create_permutations

if TYPE_CHECKING:
    from rubiks_cube.configuration.types import CubePermutation


PIECE_MASK = np.zeros(54, dtype="bool")
for i in [0, 1, 2, 3, 5, 6, 7, 12, 14, 30, 32, 45, 46, 47, 48, 50, 51, 52]:
    PIECE_MASK[i] = True


def corner_trace(permutation: CubePermutation) -> str:
    """Return the corner cycles.

    Args:
        permutation (CubePermutation): Cube permutation.

    Returns:
        str: Corner cycles.
    """
    # Define the corners and their idxs
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
        current_conrner_idxs = corner_idxs.copy()

        cycle = 0
        while current_conrner_idxs[0] not in explored_corners:
            explored_corners.update(set(current_conrner_idxs))
            current_conrner_idxs = list(permutation[current_conrner_idxs])
            cycle += 1

        if cycle > 1:
            cycles.append(cycle)

    return "".join([str(n) + "c" for n in sorted(cycles, reverse=True)])


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
            explored_edges.update(set(current_edge_idxs))
            cycle += 1
            current_edge_idxs = list(permutation[current_edge_idxs])

        if cycle > 1:
            cycles.append(cycle)

    return "".join([str(n) + "e" for n in sorted(cycles, reverse=True)])


# TODO: This works, but should be replaced with a non-stochastic method!
# If uses on average ~2 moves to differentiate between real/fake HTR
# It recognizes if it is real/fake HTR by corner-tracing
def distinguish_htr(permutation: CubePermutation) -> str:
    """Distinguish between real and fake HTR patterns.

    Args:
        permutation (CubePermutation): Cube permutation.

    Returns:
        str: "htr" or "fake-htr".
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

    return_tag = "htr-like"

    while return_tag == "htr-like":
        trace = corner_trace(current_permutation)
        if trace in real_htr_traces:
            return_tag = "htr"
        elif trace in fake_htr_traces:
            return_tag = "fake-htr"
        else:
            move = rng.choice(["L2", "R2", "U2", "D2", "F2", "B2"], size=1)[0]
            current_permutation = current_permutation[permutations[move]]

    return return_tag
