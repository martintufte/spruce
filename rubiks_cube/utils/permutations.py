import numpy as np

from rubiks_cube.utils.sequence import Sequence
from rubiks_cube.utils.move import is_rotation


SOLVED_STATE = np.arange(54, dtype="int")

MASK_PIECES = np.zeros(54, dtype="bool")
for i in [0, 1, 2, 3, 5, 6, 7, 12, 14, 30, 32, 45, 46, 47, 48, 50, 51, 52]:
    MASK_PIECES[i] = True


def rotate(permutation: np.ndarray, k=1) -> np.ndarray:
    """Rotate the permutation 90 degrees counterclock wise."""

    assert (
        np.floor(np.sqrt(permutation.size)) ** 2 == permutation.size
    ), "array must be square!"
    sqrt = np.sqrt(permutation.size).astype("int")

    return np.rot90(permutation.reshape((sqrt, sqrt)), k).flatten()


def inverse(permutation: np.ndarray) -> np.ndarray:
    """Return the inverse permutation."""

    inv_permutation = np.empty_like(permutation)
    inv_permutation[permutation] = np.arange(permutation.size)
    return inv_permutation


def multiply(permutation: np.ndarray, factor=2) -> np.ndarray:
    """Return the permutation applied multiple times."""

    assert isinstance(factor, int) and factor > 0, "invalid factor!"

    mul_permutation = permutation
    for _ in range(factor - 1):
        mul_permutation = mul_permutation[permutation]

    return mul_permutation


def corner_cycles(permutation: np.ndarray) -> str:
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

    return "".join([str(n) + "C" for n in sorted(cycles, reverse=True)])


def edge_cycles(permutation: np.ndarray) -> str:
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

    return "".join([str(n) + "E" for n in sorted(cycles, reverse=True)])


def blind_trace(permutation: np.ndarray) -> str:
    """Return the blind trace of the cube state. Assume no rotations!"""

    return corner_cycles(permutation) + edge_cycles(permutation)


def add_connection(connection, from_node, to_node) -> None:
    """Add a connection to the connection dictionary."""
    if from_node in connection:
        connection[from_node].append(to_node)
    else:
        connection[from_node] = [to_node]


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


def block_trace(permutation: np.ndarray) -> str:
    """Return the block trace of the cube state. Assume no rotations!"""

    xe_face, ec_face = find_connected_face(permutation)
    ec_cube = edge_corner_block(ec_face)
    xe_cube = center_edge_block(xe_face)

    # number of 2x1 blocks
    n_blocks = len(ec_cube.split(" ")) + len(xe_cube.split(" "))

    return "2x1 blocks: " + str(n_blocks)


def is_solved(p: np.ndarray) -> bool:
    """Return True if the permutation is solved. Assume no rotations!"""

    return np.array_equal(p, SOLVED_STATE)


def count_solved(p: np.ndarray) -> int:
    """Return the number of solved pieces. Assume no rotations!"""
    return np.sum(p[MASK_PIECES] == SOLVED_STATE[MASK_PIECES])


def count_similar(p: np.ndarray, q: np.ndarray) -> int:
    """Return the number of similar pieces. Assume no rotations!"""
    return np.sum(p[MASK_PIECES] == q[MASK_PIECES])


def get_permutation_dictionary(n: int) -> dict:
    """Return a dictionaty over all legal turns."""

    assert n >= 2, "n must be minimum size 2."
    assert isinstance(n, int), "n must be integer"

    # Define the identity permutation
    n2 = n**2
    identity = np.arange(6 * n2)

    # Define cube faces slices
    up = slice(0, n2)
    front = slice(n2, 2 * n2)
    right = slice(2 * n2, 3 * n2)
    back = slice(3 * n2, 4 * n2)
    left = slice(4 * n2, 5 * n2)
    down = slice(5 * n2, 6 * n2)

    # Define cube rotation x
    x = np.copy(identity)
    x[up] = identity[front]
    x[front] = identity[down]
    x[right] = rotate(identity[right], -1)
    x[back] = rotate(identity[up], 2)
    x[left] = rotate(identity[left], 1)
    x[down] = rotate(identity[back], 2)

    # Define cube rotation y
    y = np.copy(identity)
    y[up] = rotate(identity[up], -1)
    y[front] = identity[right]
    y[right] = identity[back]
    y[back] = identity[left]
    y[left] = identity[front]
    y[down] = rotate(identity[down], 1)

    # Define Up face rotations (U, Uw, 2Uw, ... (n-1)Uw)
    Us = []
    for i in range(1, n):
        U = np.copy(identity)
        affected = slice(0, i * n)
        U[up] = rotate(identity[up], -1)
        U[front][affected] = identity[right][affected]
        U[right][affected] = identity[back][affected]
        U[back][affected] = identity[left][affected]
        U[left][affected] = identity[front][affected]
        Us.append(U)

    # Define all other permutations from I, U, x, y
    # Rotations with doubles and inverses
    # x (defined)
    x2 = multiply(x, 2)
    xi = inverse(x)
    # y (defined)
    y2 = multiply(y, 2)
    yi = inverse(y)
    z = identity[x][y][xi]
    z2 = multiply(z, 2)
    zi = inverse(z)

    # Face turns with inverses and doubles
    # Us (defined)
    Fs = [identity[x][U][xi] for U in Us]
    Rs = [identity[zi][U][z] for U in Us]
    Bs = [identity[xi][U][x] for U in Us]
    Ls = [identity[z][U][zi] for U in Us]
    Ds = [identity[x2][U][x2] for U in Us]

    Us_inv = [inverse(p) for p in Us]
    Fs_inv = [inverse(p) for p in Fs]
    Rs_inv = [inverse(p) for p in Rs]
    Bs_inv = [inverse(p) for p in Bs]
    Ls_inv = [inverse(p) for p in Ls]
    Ds_inv = [inverse(p) for p in Ds]

    Us_double = [multiply(p, 2) for p in Us]
    Fs_double = [multiply(p, 2) for p in Fs]
    Rs_double = [multiply(p, 2) for p in Rs]
    Bs_double = [multiply(p, 2) for p in Bs]
    Ls_double = [multiply(p, 2) for p in Ls]
    Ds_double = [multiply(p, 2) for p in Ds]

    # Slice turns
    M = identity[Rs[0]][Rs_inv[-1]]
    M2 = multiply(M, 2)
    Mi = inverse(M)
    S = identity[Fs[-1]][Fs_inv[0]]
    S2 = multiply(S, 2)
    Si = inverse(S)
    E = identity[Us[0]][Us_inv[-1]]
    E2 = multiply(E, 2)
    Ei = inverse(E)

    # Define the return dictionary with rotations
    # Include slice moves for 3x3 and higher!
    return_dic = {
        "x": x,
        "x2": x2,
        "x'": xi,
        "y": y,
        "y2": y2,
        "y'": yi,
        "z": z,
        "z2": z2,
        "z'": zi,
    }
    if n > 2:
        return_dic.update(
            {
                "M": M,
                "M2": M2,
                "M'": Mi,
                "S": S,
                "S2": S2,
                "S'": Si,
                "E": E,
                "E2": E2,
                "E'": Ei,
            }
        )
    if n == 4:
        # Inner slice turns for 4x4
        r = identity[Rs[1]][Rs_inv[0]]
        r2 = multiply(r, 2)
        ri = inverse(r)
        el = identity[Ls[1]][Ls_inv[0]]
        l2 = multiply(el, 2)
        li = inverse(el)
        return_dic.update(
            {"r": r, "r2": r2, "r'": ri, "l": el, "l2": l2, "l'": li}
        )

    # Add Face turns
    for i, (p, pi, p2) in enumerate(zip(Us, Us_inv, Us_double), start=1):
        base_str = str(i) + "Uw" if i > 2 else "Uw" if i == 2 else "U"
        return_dic.update(
            {base_str: p, base_str + "'": pi, base_str + "2": p2}
        )
    for i, (p, pi, p2) in enumerate(zip(Fs, Fs_inv, Fs_double), start=1):
        base_str = str(i) + "Fw" if i > 2 else "Fw" if i == 2 else "F"
        return_dic.update(
            {base_str: p, base_str + "'": pi, base_str + "2": p2}
        )
    for i, (p, pi, p2) in enumerate(zip(Rs, Rs_inv, Rs_double), start=1):
        base_str = str(i) + "Rw" if i > 2 else "Rw" if i == 2 else "R"
        return_dic.update(
            {base_str: p, base_str + "'": pi, base_str + "2": p2}
        )
    for i, (p, pi, p2) in enumerate(zip(Bs, Bs_inv, Bs_double), start=1):
        base_str = str(i) + "Bw" if i > 2 else "Bw" if i == 2 else "B"
        return_dic.update(
            {base_str: p, base_str + "'": pi, base_str + "2": p2}
        )
    for i, (p, pi, p2) in enumerate(zip(Ls, Ls_inv, Ls_double), start=1):
        base_str = str(i) + "Lw" if i > 2 else "Lw" if i == 2 else "L"
        return_dic.update(
            {base_str: p, base_str + "'": pi, base_str + "2": p2}
        )
    for i, (p, pi, p2) in enumerate(zip(Ds, Ds_inv, Ds_double), start=1):
        base_str = str(i) + "Dw" if i > 2 else "Dw" if i == 2 else "D"
        return_dic.update(
            {base_str: p, base_str + "'": pi, base_str + "2": p2}
        )

    return return_dic


PERMUTATIONS = get_permutation_dictionary(3)


def get_permutation(
    sequence: Sequence,
    ignore_rotations: bool = False,
    from_permutation: np.ndarray = SOLVED_STATE,
) -> np.ndarray:
    """Get a cube permutation."""

    permutation = from_permutation.copy()

    for move in sequence:
        if move.startswith("("):
            raise ValueError("Cannot get cube permutation of niss!")
        elif ignore_rotations and is_rotation(move):
            continue
        else:
            permutation = permutation[PERMUTATIONS[move]]

    return permutation


def apply_move(permutation, move) -> np.ndarray:
    """Apply a move to the permutation."""
    return permutation[PERMUTATIONS[move]]


def apply_moves(permutation, sequence: Sequence) -> np.ndarray:
    """Apply a sequence of moves to the permutation."""
    for move in sequence:
        permutation = apply_move(permutation, move)

    return permutation
