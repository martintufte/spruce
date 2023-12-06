import numpy as np
from utils.sequence import Sequence, is_rotation

SOLVED = np.arange(54)

MASK_PIECES = np.zeros(54, dtype="bool")
for i in [0, 1, 2, 3, 5, 6, 7, 12, 14,
          30, 32, 45, 46, 47, 48, 50, 51, 52]:
    MASK_PIECES[i] = True


def rotate(permutation: np.ndarray, k=1) -> np.ndarray:
    """Rotate the permutation 90 degrees counterclock wise."""

    assert np.floor(np.sqrt(permutation.size))**2 == permutation.size, \
        "array must be square!"
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
    for _ in range(factor-1):
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
        # cube_list = ["G"] * 54
        # plot cube
        # for idx in corner_idxs:
        #     cube_list[idx] = "R"
        # cube_string = "".join(cube_list)
        # cube = np.array(list(cube_string), dtype=np.str_)
        # fig = plot_cube_state(initial_state=cube)
        # st.pyplot(fig, use_container_width=True)

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
        # plot cube
        # cube_list = ["G"] * 54
        # for idx in edge_idxs:
        #     cube_list[idx] = "R"
        # cube_string = "".join(cube_list)
        # cube = np.array(list(cube_string), dtype=np.str_)
        # fig = plot_cube_state(initial_state=cube)
        # st.pyplot(fig, use_container_width=True)

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


def is_solved(p: np.ndarray) -> bool:
    """Return True if the permutation is solved. Assume no rotations!"""

    return np.array_equal(p, SOLVED)


def count_solved(p: np.ndarray) -> int:
    """Return the number of solved pieces. Assume no rotations!"""
    return np.sum(p[MASK_PIECES] == SOLVED[MASK_PIECES])


def count_similar(p: np.ndarray, q: np.ndarray) -> int:
    """Return the number of similar pieces. Assume no rotations!"""
    return np.sum(p[MASK_PIECES] == q[MASK_PIECES])


def get_permutations(n: int) -> dict:
    """Return a dictionaty over all legal turns."""

    assert n >= 2, "n must be minimum size 2."
    assert isinstance(n, int), "n must be integer"

    # Define the identity permutation
    n2 = n**2
    identity = np.arange(6*n2)

    # Define cube faces slices
    up = slice(0, n2)
    front = slice(n2, 2*n2)
    right = slice(2*n2, 3*n2)
    back = slice(3*n2, 4*n2)
    left = slice(4*n2, 5*n2)
    down = slice(5*n2, 6*n2)

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
        affected = slice(0, i*n)
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
        "x": x, "x2": x2, "x'": xi,
        "y": y, "y2": y2, "y'": yi,
        "z": z, "z2": z2, "z'": zi,
    }
    if n > 2:
        return_dic.update({
            "M": M, "M2": M2, "M'": Mi,
            "S": S, "S2": S2, "S'": Si,
            "E": E, "E2": E2, "E'": Ei,
        })
    if n == 4:
        # Inner slice turns for 4x4
        r = identity[Rs[1]][Rs_inv[0]]
        r2 = multiply(r, 2)
        ri = inverse(r)
        el = identity[Ls[1]][Ls_inv[0]]
        l2 = multiply(el, 2)
        li = inverse(el)
        return_dic.update({
            "r": r, "r2": r2, "r'": ri,
            "l": el, "l2": l2, "l'": li
        })

    # Add Face turns
    for i, (p, pi, p2) in enumerate(zip(Us, Us_inv, Us_double), start=1):
        base_str = str(i)+"Uw" if i > 2 else "Uw" if i == 2 else "U"
        return_dic.update({base_str: p, base_str+"'": pi, base_str+"2": p2})
    for i, (p, pi, p2) in enumerate(zip(Fs, Fs_inv, Fs_double), start=1):
        base_str = str(i)+"Fw" if i > 2 else "Fw" if i == 2 else "F"
        return_dic.update({base_str: p, base_str+"'": pi, base_str+"2": p2})
    for i, (p, pi, p2) in enumerate(zip(Rs, Rs_inv, Rs_double), start=1):
        base_str = str(i)+"Rw" if i > 2 else "Rw" if i == 2 else "R"
        return_dic.update({base_str: p, base_str+"'": pi, base_str+"2": p2})
    for i, (p, pi, p2) in enumerate(zip(Bs, Bs_inv, Bs_double), start=1):
        base_str = str(i)+"Bw" if i > 2 else "Bw" if i == 2 else "B"
        return_dic.update({base_str: p, base_str+"'": pi, base_str+"2": p2})
    for i, (p, pi, p2) in enumerate(zip(Ls, Ls_inv, Ls_double), start=1):
        base_str = str(i)+"Lw" if i > 2 else "Lw" if i == 2 else "L"
        return_dic.update({base_str: p, base_str+"'": pi, base_str+"2": p2})
    for i, (p, pi, p2) in enumerate(zip(Ds, Ds_inv, Ds_double), start=1):
        base_str = str(i)+"Dw" if i > 2 else "Dw" if i == 2 else "D"
        return_dic.update({base_str: p, base_str+"'": pi, base_str+"2": p2})

    return return_dic


PERMUTATIONS = get_permutations(3)


def get_cube_permutation(
        sequence: Sequence,
        ignore_rotations: bool = False,
) -> np.ndarray:
    """Get a cube permutation."""

    permutation = np.copy(SOLVED)

    for move in sequence:
        if move.startswith("("):
            raise ValueError("Cannot get cube permutation of niss!")
        elif ignore_rotations and is_rotation(move):
            continue
        else:
            permutation = permutation[PERMUTATIONS[move]]

    return permutation


def apply_moves(permutation, sequence: Sequence):
    """Apply a sequence of moves to the permutation."""
    for move in sequence:
        permutation = permutation[PERMUTATIONS[move]]

    return permutation


if __name__ == "__main__":
    raise RuntimeError("This module should not be run directly!")
