import hashlib
from numba import njit
import numpy as np


class CubeState():
    """Third iteration cube state model with numpy arrays."""

    def __init__(self, sequence: list | None = None):
        """Initialize cube state."""
        self.ep = np.arange(12, dtype=np.int8)
        self.cp = np.arange(8, dtype=np.int8)
        self.eo = np.zeros(12, dtype=np.int8)
        self.co = np.zeros(8, dtype=np.int8)

        self.move_functions = {
            "U": u,
            "U'": u_prime,
            "U2": u2,
            "D": d,
            "D'": d_prime,
            "D2": d2,
            "F": f,
            "F'": f_prime,
            "F2": f2,
            "B": b,
            "B'": b_prime,
            "B2": b2,
            "L": ll,
            "L'": l_prime,
            "L2": l2,
            "R": r,
            "R'": r_prime,
            "R2": r2,
        }

        if sequence is not None:
            for move in sequence:
                self.move_functions[move](
                    self.ep,
                    self.eo,
                    self.cp,
                    self.co,
                )

    def __str__(self):
        """Return cube state as string."""
        return (
            f"ep: {self.ep}\n"
            f"eo: {self.eo[self.ep] % 2}\n"
            f"cp: {self.cp}\n"
            f"co: {self.co[self.cp] % 3}\n"
        )

    def __repr__(self):
        return self.__str__()

    def __copy__(self):
        """Return copy of cube state."""
        new = CubeState()
        new.set_ep(self.ep)
        new.set_eo(self.eo)
        new.set_cp(self.cp)
        new.set_co(self.co)
        return new

    def __eq__(self, other):
        """Return True if cube states are equal."""
        return (
            np.array_equal(self.ep, other.ep)
            and np.array_equal(self.cp, other.cp)
            and np.array_equal(self.eo, other.eo)
            and np.array_equal(self.co, other.co)
        )

    def set_ep(self, ep):
        """Set edge permutation."""
        self.ep = np.array(ep, dtype=np.int8)

    def set_cp(self, cp):
        """Set corner permutation."""
        self.cp = np.array(cp, dtype=np.int8)

    def set_eo(self, eo):
        """Set edge orientation."""
        self.eo = np.array(eo, dtype=np.int8)

    def set_co(self, co):
        """Set corner orientation."""
        self.co = np.array(co, dtype=np.int8)

    def get_ep(self):
        """Get edge permutation."""
        return list(self.ep)

    def get_cp(self):
        """Get corner permutation."""
        return list(self.cp)

    def get_eo(self):
        """Get edge orientation."""
        return list(self.eo[self.ep] % 2)

    def get_co(self):
        """Get corner orientation."""
        return list(self.co[self.cp] % 3)

    def hash(self):
        """Return hash of cube state."""
        return hashlib.md5(
            np.concatenate(
                (
                    self.ep,
                    self.eo,
                    self.cp,
                    self.co,
                )
            ).tobytes()
        ).hexdigest()

    def apply(self, move):
        """Apply move to cube state."""

        self.move_functions[move](
            self.ep,
            self.eo,
            self.cp,
            self.co,
        )


@njit(cache=True)
def u(ep: np.ndarray, eo: np.ndarray, cp: np.ndarray, co: np.ndarray):
    """Apply U move to cube state."""
    f = np.array([0, 1, 2, 3])
    g = np.array([3, 0, 1, 2])

    ep[f] = ep[g]
    cp[f] = cp[g]


@njit(cache=True)
def u_prime(ep: np.ndarray, eo: np.ndarray, cp: np.ndarray, co: np.ndarray):
    """Apply U' move to cube state."""
    f = np.array([0, 1, 2, 3])
    g = np.array([1, 2, 3, 0])

    ep[f] = ep[g]
    cp[f] = cp[g]


@njit(cache=True)
def u2(ep: np.ndarray, eo: np.ndarray, cp: np.ndarray, co: np.ndarray):
    """Apply U2 move to cube state."""
    f = np.array([0, 1, 2, 3])
    g = np.array([2, 3, 0, 1])

    ep[f] = ep[g]
    cp[f] = cp[g]


@njit(cache=True)
def d(ep: np.ndarray, eo: np.ndarray, cp: np.ndarray, co: np.ndarray):
    """Apply D move to cube state."""
    f = np.array([8, 9, 10, 11])
    g = np.array([11, 8, 9, 10])
    h = np.array([4, 5, 6, 7])
    i = np.array([7, 4, 5, 6])

    ep[f] = ep[g]
    cp[h] = cp[i]


@njit(cache=True)
def d_prime(ep: np.ndarray, eo: np.ndarray, cp: np.ndarray, co: np.ndarray):
    """Apply D' move to cube state."""
    f = np.array([8, 9, 10, 11])
    g = np.array([9, 10, 11, 8])
    h = np.array([4, 5, 6, 7])
    i = np.array([5, 6, 7, 4])

    ep[f] = ep[g]
    cp[h] = cp[i]


@njit(cache=True)
def d2(ep: np.ndarray, eo: np.ndarray, cp: np.ndarray, co: np.ndarray):
    """Apply D2 move to cube state."""
    f = np.array([8, 9, 10, 11])
    g = np.array([10, 11, 8, 9])
    h = np.array([4, 5, 6, 7])
    i = np.array([6, 7, 4, 5])

    ep[f] = ep[g]
    cp[h] = cp[i]


@njit(cache=True)
def f(ep: np.ndarray, eo: np.ndarray, cp: np.ndarray, co: np.ndarray):
    """Apply F move to cube state."""
    f = np.array([2, 5, 8, 6])
    g = np.array([6, 2, 5, 8])
    h = np.array([3, 2, 5, 4])
    i = np.array([4, 3, 2, 5])
    j = np.array([2, 4])
    k = np.array([3, 5])

    ep[f] = ep[g]
    cp[h] = cp[i]

    eo[ep[f]] += 1
    co[cp[j]] += 1
    co[cp[k]] += 2


@njit(cache=True)
def f_prime(ep: np.ndarray, eo: np.ndarray, cp: np.ndarray, co: np.ndarray):
    """Apply F' move to cube state."""
    f = np.array([2, 5, 8, 6])
    g = np.array([5, 8, 6, 2])
    h = np.array([3, 2, 5, 4])
    i = np.array([2, 5, 4, 3])
    j = np.array([2, 4])
    k = np.array([3, 5])

    ep[f] = ep[g]
    cp[h] = cp[i]

    eo[ep[f]] += 1
    co[cp[j]] += 1
    co[cp[k]] += 2


@njit(cache=True)
def f2(ep: np.ndarray, eo: np.ndarray, cp: np.ndarray, co: np.ndarray):
    """Apply F2 move to cube state."""
    f = np.array([2, 5, 8, 6])
    g = np.array([8, 6, 2, 5])
    h = np.array([3, 2, 5, 4])
    i = np.array([5, 4, 3, 2])

    ep[f] = ep[g]
    cp[h] = cp[i]


@njit(cache=True)
def b(ep: np.ndarray, eo: np.ndarray, cp: np.ndarray, co: np.ndarray):
    """Apply B move to cube state."""
    f = np.array([0, 7, 10, 4])
    g = np.array([4, 0, 7, 10])
    h = np.array([1, 0, 7, 6])
    i = np.array([6, 1, 0, 7])
    j = np.array([0, 6])
    k = np.array([1, 7])

    ep[f] = ep[g]
    cp[h] = cp[i]

    eo[ep[f]] += 1
    co[cp[j]] += 1
    co[cp[k]] += 2


@njit(cache=True)
def b_prime(ep: np.ndarray, eo: np.ndarray, cp: np.ndarray, co: np.ndarray):
    """Apply B' move to cube state."""
    f = np.array([0, 7, 10, 4])
    g = np.array([7, 10, 4, 0])
    h = np.array([1, 0, 7, 6])
    i = np.array([0, 7, 6, 1])
    j = np.array([0, 6])
    k = np.array([1, 7])

    ep[f] = ep[g]
    cp[h] = cp[i]

    eo[ep[f]] += 1
    co[cp[j]] += 1
    co[cp[k]] += 2


@njit(cache=True)
def b2(ep: np.ndarray, eo: np.ndarray, cp: np.ndarray, co: np.ndarray):
    """Apply B2 move to cube state."""
    f = np.array([0, 7, 10, 4])
    g = np.array([10, 4, 0, 7])
    h = np.array([1, 0, 7, 6])
    i = np.array([7, 6, 1, 0])

    ep[f] = ep[g]
    cp[h] = cp[i]


@njit(cache=True)
def ll(ep: np.ndarray, eo: np.ndarray, cp: np.ndarray, co: np.ndarray):
    """Apply L move to cube state."""
    f = np.array([3, 6, 11, 7])
    g = np.array([7, 3, 6, 11])
    h = np.array([0, 3, 4, 7])
    i = np.array([7, 0, 3, 4])
    j = np.array([0, 4])
    k = np.array([3, 7])

    ep[f] = ep[g]
    cp[h] = cp[i]

    co[cp[j]] += 2
    co[cp[k]] += 1


@njit(cache=True)
def l_prime(ep: np.ndarray, eo: np.ndarray, cp: np.ndarray, co: np.ndarray):
    """Apply L' move to cube state."""
    f = np.array([3, 6, 11, 7])
    g = np.array([6, 11, 7, 3])
    h = np.array([0, 3, 4, 7])
    i = np.array([3, 4, 7, 0])
    j = np.array([0, 4])
    k = np.array([3, 7])

    ep[f] = ep[g]
    cp[h] = cp[i]

    co[cp[j]] += 2
    co[cp[k]] += 1


@njit(cache=True)
def l2(ep: np.ndarray, eo: np.ndarray, cp: np.ndarray, co: np.ndarray):
    """Apply L2 move to cube state."""
    f = np.array([3, 6, 11, 7])
    g = np.array([11, 7, 3, 6])
    h = np.array([0, 3, 4, 7])
    i = np.array([4, 7, 0, 3])

    ep[f] = ep[g]
    cp[h] = cp[i]


@njit(cache=True)
def r(ep: np.ndarray, eo: np.ndarray, cp: np.ndarray, co: np.ndarray):
    """Apply R move to cube state."""
    f = np.array([1, 4, 9, 5])
    g = np.array([5, 1, 4, 9])
    h = np.array([2, 1, 6, 5])
    i = np.array([5, 2, 1, 6])
    j = np.array([1, 5])
    k = np.array([2, 6])

    ep[f] = ep[g]
    cp[h] = cp[i]

    co[cp[j]] += 1
    co[cp[k]] += 2


@njit(cache=True)
def r_prime(ep: np.ndarray, eo: np.ndarray, cp: np.ndarray, co: np.ndarray):
    """Apply R' move to cube state."""
    f = np.array([1, 4, 9, 5])
    g = np.array([4, 9, 5, 1])
    h = np.array([2, 1, 6, 5])
    i = np.array([1, 6, 5, 2])
    j = np.array([1, 5])
    k = np.array([2, 6])

    ep[f] = ep[g]
    cp[h] = cp[i]

    co[cp[j]] += 1
    co[cp[k]] += 2


@njit(cache=True)
def r2(ep: np.ndarray, eo: np.ndarray, cp: np.ndarray, co: np.ndarray):
    """Apply R2 move to cube state."""
    f = np.array([1, 4, 9, 5])
    g = np.array([9, 5, 1, 4])
    h = np.array([2, 1, 6, 5])
    i = np.array([6, 5, 2, 1])

    ep[f] = ep[g]
    cp[h] = cp[i]
