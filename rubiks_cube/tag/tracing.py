import numpy as np

from rubiks_cube.configuration.types import CubeState

PIECE_MASK = np.zeros(54, dtype="bool")
for i in [0, 1, 2, 3, 5, 6, 7, 12, 14, 30, 32, 45, 46, 47, 48, 50, 51, 52]:
    PIECE_MASK[i] = True


def corner_trace(state: CubeState) -> str:
    """Return the corner cycles.

    Args:
        state (CubeState): Cube state.

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

        cycle = 0
        while corner_idxs[0] not in explored_corners:
            explored_corners.update(set(corner_idxs))
            corner_idxs = list(state[corner_idxs])
            cycle += 1

        if cycle > 1:
            cycles.append(cycle)
        # elif cycle == 1 and state[corner_idxs[0]] != corner_idxs[0]:
        #     cycles.append(1)

    return "".join([str(n) + "c" for n in sorted(cycles, reverse=True)])


def edge_trace(state: CubeState) -> str:
    """Return the edge cycles.

    Args:
        state (CubeState): Cube state.

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

        cycle = 0
        while edge_idxs[0] not in explored_edges:
            explored_edges.update(set(edge_idxs))
            cycle += 1
            edge_idxs = list(state[edge_idxs])

        if cycle > 1:
            cycles.append(cycle)

        # Add flipped edges to the list of cycles
        # elif cycle == 1 and state[current_edge] != current_edge:
        #     cycles.append(1)

    return "".join([str(n) + "e" for n in sorted(cycles, reverse=True)])
