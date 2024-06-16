import numpy as np

from rubiks_cube.configuration import CUBE_SIZE

SOLVED_STATE = np.arange(6 * CUBE_SIZE**2, dtype="int")
PIECE_MASK = np.zeros(54, dtype="bool")

for i in [0, 1, 2, 3, 5, 6, 7, 12, 14, 30, 32, 45, 46, 47, 48, 50, 51, 52]:
    PIECE_MASK[i] = True


def corner_trace(permutation: np.ndarray) -> str:
    """Return the corner cycles."""

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
            corner_idxs = permutation[corner_idxs]
            cycle += 1

        if cycle > 1:
            cycles.append(cycle)
        # elif cycle == 1 and permutation[corner_idxs[0]] != corner_idxs[0]:
        #     cycles.append(1)

    return "".join([str(n) + "c" for n in sorted(cycles, reverse=True)])


def edge_trace(permutation: np.ndarray) -> str:
    """Return the edge cycles."""

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
            edge_idxs = permutation[edge_idxs]

        if cycle > 1:
            cycles.append(cycle)

        # Add flipped edges to the list of cycles
        # elif cycle == 1 and permutation[current_edge] != current_edge:
        #     cycles.append(1)

    return "".join([str(n) + "e" for n in sorted(cycles, reverse=True)])


# Remove
def blind_trace(permutation: np.ndarray) -> str:
    """Return the blind trace of the cube state. Assume no rotations!"""

    return corner_trace(permutation) + edge_trace(permutation)


# Remove
def add_connection(connection, from_node, to_node) -> None:
    """Add a connection to the connection dictionary."""
    if from_node in connection:
        connection[from_node].append(to_node)
    else:
        connection[from_node] = [to_node]


# Remove
def find_connected_face(permutation: np.ndarray) -> tuple[dict, dict]:
    """Return the connected idxs of the cube state. Assume no rotations!"""
    center_edge_connections = {
        4: [1, 3, 5, 7],
        13: [10, 12, 14, 16],
        22: [19, 21, 23, 25],
        31: [28, 30, 32, 34],
        40: [37, 39, 41, 43],
        49: [46, 48, 50, 52],
    }
    edge_corner_connections = {
        1: [0, 2],
        3: [0, 6],
        5: [2, 8],
        7: [6, 8],
        10: [9, 11],
        12: [9, 15],
        14: [11, 17],
        16: [15, 17],
        19: [18, 20],
        21: [18, 24],
        23: [20, 26],
        25: [24, 26],
        28: [27, 29],
        30: [27, 33],
        32: [29, 35],
        34: [33, 35],
        37: [36, 38],
        39: [36, 42],
        41: [38, 44],
        43: [42, 44],
        46: [45, 47],
        48: [45, 51],
        50: [47, 53],
        52: [51, 53],
    }
    cube_string = "U" * 9 + "F" * 9 + "R" * 9 + "B" * 9 + "L" * 9 + "D" * 9
    cube = np.array(list(cube_string), dtype=np.str_)

    # Keep track of all connections
    xe_connections = {}
    ec_connections = {}

    # Find center-edge blocks
    for center, edge_list in center_edge_connections.items():
        for edge in edge_list:
            if cube[permutation[center]] == cube[permutation[edge]]:
                add_connection(xe_connections, center, edge)
                add_connection(xe_connections, edge, center)

    # Find edge-corner blocks
    for edge, corner_list in edge_corner_connections.items():
        for corner in corner_list:
            if cube[permutation[edge]] == cube[permutation[corner]]:
                add_connection(ec_connections, edge, corner)
                add_connection(ec_connections, corner, edge)

    return xe_connections, ec_connections


# Remove
def edge_corner_block(ec_connections: dict) -> str:
    """Find the block trace of the cube state. Assume no rotations!"""

    ordered_corners = {
        "UBL": [0, 29, 36],
        "UFL": [6, 9, 38],
        "UBR": [2, 27, 20],
        "UFR": [8, 11, 18],
        "DBL": [51, 35, 42],
        "DFL": [45, 15, 44],
        "DBR": [53, 33, 26],
        "DFR": [47, 17, 24],
    }
    ordered_edges = {
        "UB": [1, 28],
        "UL": [3, 37],
        "UR": [5, 19],
        "UF": [7, 10],
        "BL": [32, 39],
        "FL": [12, 41],
        "BR": [30, 23],
        "FR": [14, 21],
        "DB": [52, 34],
        "DL": [48, 43],
        "DR": [50, 25],
        "DF": [46, 16],
    }
    edge_corner_connections = {
        "UB": ["UBL", "UBR"],
        "UL": ["UBL", "UFL"],
        "UR": ["UBR", "UFR"],
        "UF": ["UFL", "UFR"],
        "BL": ["UBL", "DBL"],
        "FL": ["UFL", "DFL"],
        "BR": ["UBR", "DBR"],
        "FR": ["UFR", "DFR"],
        "DB": ["DBL", "DBR"],
        "DL": ["DBL", "DFL"],
        "DR": ["DBR", "DFR"],
        "DF": ["DFL", "DFR"],
    }

    actual_ec_connections = {}
    # Keep track of explored edges and cycles
    for edge, corners in edge_corner_connections.items():
        for corner in corners:
            connected = True
            for face in edge:
                i = edge.index(face)
                j = corner.index(face)
                edge_idx = ordered_edges[edge][i]
                corner_idx = ordered_corners[corner][j]
                if edge_idx not in ec_connections.keys():
                    connected = False
                    break
                elif corner_idx not in ec_connections[edge_idx]:
                    connected = False
                    break
            if connected:
                add_connection(actual_ec_connections, edge, corner)

    string = ""
    for edge, corner in actual_ec_connections.items():
        string += str(edge) + "-" + str(corner) + " "
    return string


# Remove
def center_edge_block(xe_connections: dict) -> str:
    """Find the block trace of the cube state. Assume no rotations!"""
    ordered_edges = {
        "UB": [1, 28],
        "UL": [3, 37],
        "UR": [5, 19],
        "UF": [7, 10],
        "BL": [32, 39],
        "FL": [12, 41],
        "BR": [30, 23],
        "FR": [14, 21],
        "DB": [52, 34],
        "DL": [48, 43],
        "DR": [50, 25],
        "DF": [46, 16],
    }
    ordered_centers = {
        "U": 4,
        "F": 13,
        "R": 22,
        "B": 31,
        "L": 40,
        "D": 49,
    }
    corner_edge_connection = {
        "U": ["UB", "UL", "UR", "UF"],
        "F": ["UF", "FR", "FL", "DF"],
        "R": ["UR", "FR", "BR", "DR"],
        "B": ["UB", "BR", "BL", "DB"],
        "L": ["UL", "BL", "FL", "DL"],
        "D": ["DB", "DL", "DR", "DF"],
    }
    xe_cube = {}
    for center, edges in corner_edge_connection.items():
        for edge in edges:
            connected = True
            j = edge.index(center)
            center_idx = ordered_centers[center]
            edge_idx = ordered_edges[edge][j]
            if center_idx not in xe_connections.keys():
                connected = False
            elif edge_idx not in xe_connections[center_idx]:
                connected = False
            if connected:
                add_connection(xe_cube, center, edge)

    string = ""
    for center, edge in xe_cube.items():
        string += str(center) + "-" + str(edge) + " "
    return string


# Remove
def block_trace(permutation: np.ndarray) -> str:
    """Return the block trace of the cube state. Assume no rotations!"""

    xe_face, ec_face = find_connected_face(permutation)
    ec_cube = edge_corner_block(ec_face)
    xe_cube = center_edge_block(xe_face)

    # number of 2x1 blocks
    n_blocks = len(ec_cube.split(" ")) + len(xe_cube.split(" "))

    return "2x1 blocks: " + str(n_blocks)


# Remove
def is_solved(p: np.ndarray) -> bool:
    """Return True if the permutation is solved. Assume no rotations!"""

    return np.array_equal(p, SOLVED_STATE)


# Remove
def count_solved(p: np.ndarray) -> int:
    """Return the number of solved pieces. Assume no rotations!"""
    return np.sum(p[PIECE_MASK] == SOLVED_STATE[PIECE_MASK])


# Remove
def count_similar(p: np.ndarray, q: np.ndarray) -> int:
    """Return the number of similar pieces. Assume no rotations!"""
    return np.sum(p[PIECE_MASK] == q[PIECE_MASK])
