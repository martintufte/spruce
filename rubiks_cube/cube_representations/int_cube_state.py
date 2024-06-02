import numpy as np
from numba import njit

from cube_state import CubeState as RefCubeState


def list_to_integer(input_list, base=2, infer=True):
    """
    Convert list to integer. The sum of the list modulo base must be 0.
    infer: If True, removes the last element of the list.
    """
    if infer:
        input_list = input_list[1:]
    res = 0
    for j, value in enumerate(reversed(input_list)):
        res += value * (base ** j)
    return res


def integer_to_list(n, base=2, length=8, infer=True):
    """
    Convert integer to list. The sum of the list modulo base must be 0.
    infer: If True, adds the last element of the list.
    """
    if n == 0:
        return [0] * length

    result_list = []
    while n > 0:
        remainder = n % base
        result_list.append(remainder)
        n //= base

    if len(result_list) < length-1:
        result_list += [0] * (length - len(result_list) - 1)

    if infer:
        result_list.append(-sum(result_list) % base)

    return list(reversed(result_list))


class CubeState():
    """Third iteration cube state model with numpy arrays."""

    def __init__(self):
        """Initialize cube state."""
        self.ep = np.arange(12, dtype=np.int8)
        self.cp = np.arange(8, dtype=np.int8)
        self.eo: int = 0
        self.co: int = 0

        # load tables
        try:
            self.eofb = np.load("tables/eofb.npy")
        except FileNotFoundError:
            print("File not found, generating table for eofb...")
            self.generate_tables("eofb")
            self.eofb = np.load("tables/eofb.npy")

        try:
            self.coud = np.load("tables/coud.npy")
        except FileNotFoundError:
            print("File not found, generating table for coud...")
            self.generate_tables("coud")
            self.coud = np.load("tables/coud.npy")

    def generate_tables(self, table_name):
        """Generate tables for IntCubeState."""
        move_list = "U U' U2 D D' D2 F F' F2 B B' B2 L L' L2 R R' R2".split()

        if table_name == "eofb":
            eofb = np.zeros((18, 2048), dtype=int)

            for i in range(2048):
                for e, move in enumerate(move_list):
                    ref = RefCubeState()
                    ref.set_eo(integer_to_list(i, base=2, length=12))
                    ref.apply(move)
                    eofb[e, i] = list_to_integer(ref.get_eo(), base=2, infer=True)  # noqa: E501

                    assert all(a == b for a, b in zip(ref.get_eo(), integer_to_list(eofb[e, i], base=2, length=12, infer=True)))  # noqa: E501

            np.save(f"tables/{table_name}.npy", eofb)

        elif table_name == "coud":
            coud = np.zeros((18, 2187), dtype=int)

            for i in range(2187):
                for e, move in enumerate(move_list):
                    ref = RefCubeState()
                    ref.set_co(integer_to_list(i, base=3, length=8))
                    ref.apply(move)
                    co_int_after = list_to_integer(ref.get_co(), base=3, infer=True)  # noqa: E501
                    coud[e, i] = co_int_after

                    assert all(a == b for a, b in zip(ref.get_co(), integer_to_list(co_int_after, base=3, length=8, infer=True)))  # noqa: E501

            np.save(f"tables/{table_name}.npy", coud)

    def __str__(self):
        """Return cube state as string."""
        return (
            f"ep: {self.ep}\n"
            f"eo: {np.array(integer_to_list(self.eo, base=2, length=12, infer=True), dtype=np.int8)}\n"  # noqa: E501
            f"cp: {self.cp}\n"
            f"co: {np.array(integer_to_list(self.co, base=3, length=8, infer=True), dtype=np.int8)}\n"  # noqa: E501
        )

    def __repr__(self):
        return self.__str__()

    def apply(self, move):
        """Apply move to cube state."""

        match move:
            case "U":
                self.eo = self.eofb[0, self.eo]
                self.co = self.coud[0, self.co]
                u(self.ep, self.cp)
            case "U'":
                self.eo = self.eofb[1, self.eo]
                self.co = self.coud[1, self.co]
                u_prime(self.ep, self.cp)
            case "U2":
                self.eo = self.eofb[2, self.eo]
                self.co = self.coud[2, self.co]
                u2(self.ep, self.cp)
            case "D":
                self.eo = self.eofb[3, self.eo]
                self.co = self.coud[3, self.co]
                d(self.ep, self.cp)
            case "D'":
                self.eo = self.eofb[4, self.eo]
                self.co = self.coud[4, self.co]
                d_prime(self.ep, self.cp)
            case "D2":
                self.eo = self.eofb[5, self.eo]
                self.co = self.coud[5, self.co]
                d2(self.ep, self.cp)
            case "F":
                self.eo = self.eofb[6, self.eo]
                self.co = self.coud[6, self.co]
                f(self.ep, self.cp)
            case "F'":
                self.eo = self.eofb[7, self.eo]
                self.co = self.coud[7, self.co]
                f_prime(self.ep, self.cp)
            case "F2":
                self.eo = self.eofb[8, self.eo]
                self.co = self.coud[8, self.co]
                f2(self.ep, self.cp)
            case "B":
                self.eo = self.eofb[9, self.eo]
                self.co = self.coud[9, self.co]
                b(self.ep, self.cp)
            case "B'":
                self.eo = self.eofb[10, self.eo]
                self.co = self.coud[10, self.co]
                b_prime(self.ep, self.cp)
            case "B2":
                self.eo = self.eofb[11, self.eo]
                self.co = self.coud[11, self.co]
                b2(self.ep, self.cp)
            case "L":
                self.eo = self.eofb[12, self.eo]
                self.co = self.coud[12, self.co]
                ll(self.ep, self.cp)
            case "L'":
                self.eo = self.eofb[13, self.eo]
                self.co = self.coud[13, self.co]
                l_prime(self.ep, self.cp)
            case "L2":
                self.eo = self.eofb[14, self.eo]
                self.co = self.coud[14, self.co]
                l2(self.ep, self.cp)
            case "R":
                self.eo = self.eofb[15, self.eo]
                self.co = self.coud[15, self.co]
                r(self.ep, self.cp)
            case "R'":
                self.eo = self.eofb[16, self.eo]
                self.co = self.coud[16, self.co]
                r_prime(self.ep, self.cp)
            case "R2":
                self.eo = self.eofb[17, self.eo]
                self.co = self.coud[17, self.co]
                r2(self.ep, self.cp)
            case _: raise ValueError(f"Invalid move {move}")


@njit(cache=True)
def u(ep: np.ndarray, cp: np.ndarray):
    """Apply U move to cube state."""
    f = np.array([0, 1, 2, 3])
    g = np.array([3, 0, 1, 2])

    ep[f] = ep[g]
    cp[f] = cp[g]


@njit(cache=True)
def u_prime(ep: np.ndarray, cp: np.ndarray):
    """Apply U' move to cube state."""
    f = np.array([0, 1, 2, 3])
    g = np.array([1, 2, 3, 0])

    ep[f] = ep[g]
    cp[f] = cp[g]


@njit(cache=True)
def u2(ep: np.ndarray, cp: np.ndarray):
    """Apply U2 move to cube state."""
    f = np.array([0, 1, 2, 3])
    g = np.array([2, 3, 0, 1])

    ep[f] = ep[g]
    cp[f] = cp[g]


@njit(cache=True)
def d(ep: np.ndarray, cp: np.ndarray):
    """Apply D move to cube state."""
    f = np.array([8, 9, 10, 11])
    g = np.array([11, 8, 9, 10])
    h = np.array([4, 5, 6, 7])
    i = np.array([7, 4, 5, 6])

    ep[f] = ep[g]
    cp[h] = cp[i]


@njit(cache=True)
def d_prime(ep: np.ndarray, cp: np.ndarray):
    """Apply D' move to cube state."""
    f = np.array([8, 9, 10, 11])
    g = np.array([9, 10, 11, 8])
    h = np.array([4, 5, 6, 7])
    i = np.array([5, 6, 7, 4])

    ep[f] = ep[g]
    cp[h] = cp[i]


@njit(cache=True)
def d2(ep: np.ndarray, cp: np.ndarray):
    """Apply D2 move to cube state."""
    f = np.array([8, 9, 10, 11])
    g = np.array([10, 11, 8, 9])
    h = np.array([4, 5, 6, 7])
    i = np.array([6, 7, 4, 5])

    ep[f] = ep[g]
    cp[h] = cp[i]


@njit(cache=True)
def f(ep: np.ndarray, cp: np.ndarray):
    """Apply F move to cube state."""
    f = np.array([2, 5, 8, 6])
    g = np.array([6, 2, 5, 8])
    h = np.array([3, 2, 5, 4])
    i = np.array([4, 3, 2, 5])

    ep[f] = ep[g]
    cp[h] = cp[i]


@njit(cache=True)
def f_prime(ep: np.ndarray, cp: np.ndarray):
    """Apply F' move to cube state."""
    f = np.array([2, 5, 8, 6])
    g = np.array([5, 8, 6, 2])
    h = np.array([3, 2, 5, 4])
    i = np.array([2, 5, 4, 3])

    ep[f] = ep[g]
    cp[h] = cp[i]


@njit(cache=True)
def f2(ep: np.ndarray, cp: np.ndarray):
    """Apply F2 move to cube state."""
    f = np.array([2, 5, 8, 6])
    g = np.array([8, 6, 2, 5])
    h = np.array([3, 2, 5, 4])
    i = np.array([5, 4, 3, 2])

    ep[f] = ep[g]
    cp[h] = cp[i]


@njit(cache=True)
def b(ep: np.ndarray, cp: np.ndarray):
    """Apply B move to cube state."""
    f = np.array([0, 7, 10, 4])
    g = np.array([4, 0, 7, 10])
    h = np.array([1, 0, 7, 6])
    i = np.array([6, 1, 0, 7])

    ep[f] = ep[g]
    cp[h] = cp[i]


@njit(cache=True)
def b_prime(ep: np.ndarray, cp: np.ndarray):
    """Apply B' move to cube state."""
    f = np.array([0, 7, 10, 4])
    g = np.array([7, 10, 4, 0])
    h = np.array([1, 0, 7, 6])
    i = np.array([0, 7, 6, 1])

    ep[f] = ep[g]
    cp[h] = cp[i]


@njit(cache=True)
def b2(ep: np.ndarray, cp: np.ndarray):
    """Apply B2 move to cube state."""
    f = np.array([0, 7, 10, 4])
    g = np.array([10, 4, 0, 7])
    h = np.array([1, 0, 7, 6])
    i = np.array([7, 6, 1, 0])

    ep[f] = ep[g]
    cp[h] = cp[i]


@njit(cache=True)
def ll(ep: np.ndarray, cp: np.ndarray):
    """Apply L move to cube state."""
    f = np.array([3, 6, 11, 7])
    g = np.array([7, 3, 6, 11])
    h = np.array([0, 3, 4, 7])
    i = np.array([7, 0, 3, 4])

    ep[f] = ep[g]
    cp[h] = cp[i]


@njit(cache=True)
def l_prime(ep: np.ndarray, cp: np.ndarray):
    """Apply L' move to cube state."""
    f = np.array([3, 6, 11, 7])
    g = np.array([6, 11, 7, 3])
    h = np.array([0, 3, 4, 7])
    i = np.array([3, 4, 7, 0])

    ep[f] = ep[g]
    cp[h] = cp[i]


@njit(cache=True)
def l2(ep: np.ndarray, cp: np.ndarray):
    """Apply L2 move to cube state."""
    f = np.array([3, 6, 11, 7])
    g = np.array([11, 7, 3, 6])
    h = np.array([0, 3, 4, 7])
    i = np.array([4, 7, 0, 3])

    ep[f] = ep[g]
    cp[h] = cp[i]


@njit(cache=True)
def r(ep: np.ndarray, cp: np.ndarray):
    """Apply R move to cube state."""
    f = np.array([1, 4, 9, 5])
    g = np.array([5, 1, 4, 9])
    h = np.array([2, 1, 6, 5])
    i = np.array([5, 2, 1, 6])

    ep[f] = ep[g]
    cp[h] = cp[i]


@njit(cache=True)
def r_prime(ep: np.ndarray, cp: np.ndarray):
    """Apply R' move to cube state."""
    f = np.array([1, 4, 9, 5])
    g = np.array([4, 9, 5, 1])
    h = np.array([2, 1, 6, 5])
    i = np.array([1, 6, 5, 2])

    ep[f] = ep[g]
    cp[h] = cp[i]


@njit(cache=True)
def r2(ep: np.ndarray, cp: np.ndarray):
    """Apply R2 move to cube state."""
    f = np.array([1, 4, 9, 5])
    g = np.array([9, 5, 1, 4])
    h = np.array([2, 1, 6, 5])
    i = np.array([6, 5, 2, 1])

    ep[f] = ep[g]
    cp[h] = cp[i]
