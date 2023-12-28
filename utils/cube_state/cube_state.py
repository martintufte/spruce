import numpy as np
import hashlib


class CubeState():
    """First iteration cube state model with numpy arrays."""

    def __init__(self):
        """Initialize cube state."""
        self.ep = np.arange(12, dtype=np.int8)
        self.eo = np.zeros(12, dtype=np.int8)
        self.cp = np.arange(8, dtype=np.int8)
        self.co = np.zeros(8, dtype=np.int8)

    def __str__(self):
        """Return cube state as string."""
        return (
            f"ep: {self.ep}\n"
            f"eo: {self.eo}\n"
            f"cp: {self.cp}\n"
            f"co: {self.co}\n"
        )

    def __repr__(self):
        return self.__str__()

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
        return list(self.eo)

    def get_co(self):
        """Get corner orientation."""
        return list(self.co)

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

        match move:
            case "U": self.u()
            case "U'": self.u_prime()
            case "U2": self.u2()
            case "D": self.d()
            case "D'": self.d_prime()
            case "D2": self.d2()
            case "F": self.f()
            case "F'": self.f_prime()
            case "F2": self.f2()
            case "B": self.b()
            case "B'": self.b_prime()
            case "B2": self.b2()
            case "L": self.ll()
            case "L'": self.l_prime()
            case "L2": self.l2()
            case "R": self.r()
            case "R'": self.r_prime()
            case "R2": self.r2()
            case _: raise ValueError(f"Invalid move {move}")

    def u(self):
        """Apply U move to cube state."""

        self.ep[[0, 1, 2, 3]] = self.ep[[3, 0, 1, 2]]
        self.eo[[0, 1, 2, 3]] = self.eo[[3, 0, 1, 2]]
        self.cp[[0, 1, 2, 3]] = self.cp[[3, 0, 1, 2]]
        self.co[[0, 1, 2, 3]] = self.co[[3, 0, 1, 2]]

    def u_prime(self):
        """Apply U' move to cube state."""

        self.ep[[0, 1, 2, 3]] = self.ep[[1, 2, 3, 0]]
        self.eo[[0, 1, 2, 3]] = self.eo[[1, 2, 3, 0]]
        self.cp[[0, 1, 2, 3]] = self.cp[[1, 2, 3, 0]]
        self.co[[0, 1, 2, 3]] = self.co[[1, 2, 3, 0]]

    def u2(self):
        """Apply U2 move to cube state."""

        self.ep[[0, 1, 2, 3]] = self.ep[[2, 3, 0, 1]]
        self.eo[[0, 1, 2, 3]] = self.eo[[2, 3, 0, 1]]
        self.cp[[0, 1, 2, 3]] = self.cp[[2, 3, 0, 1]]
        self.co[[0, 1, 2, 3]] = self.co[[2, 3, 0, 1]]

    def d(self):
        """Apply D move to cube state."""

        self.ep[[8, 9, 10, 11]] = self.ep[[11, 8, 9, 10]]
        self.eo[[8, 9, 10, 11]] = self.eo[[11, 8, 9, 10]]
        self.cp[[4, 5, 6, 7]] = self.cp[[7, 4, 5, 6]]
        self.co[[4, 5, 6, 7]] = self.co[[7, 4, 5, 6]]

    def d_prime(self):
        """Apply D' move to cube state."""

        self.ep[[8, 9, 10, 11]] = self.ep[[9, 10, 11, 8]]
        self.eo[[8, 9, 10, 11]] = self.eo[[9, 10, 11, 8]]
        self.cp[[4, 5, 6, 7]] = self.cp[[5, 6, 7, 4]]
        self.co[[4, 5, 6, 7]] = self.co[[5, 6, 7, 4]]

    def d2(self):
        """Apply D2 move to cube state."""

        self.ep[[8, 9, 10, 11]] = self.ep[[10, 11, 8, 9]]
        self.eo[[8, 9, 10, 11]] = self.eo[[10, 11, 8, 9]]
        self.cp[[4, 5, 6, 7]] = self.cp[[6, 7, 4, 5]]
        self.co[[4, 5, 6, 7]] = self.co[[6, 7, 4, 5]]

    def f(self):
        """Apply F move to cube state."""

        self.ep[[2, 5, 8, 6]] = self.ep[[6, 2, 5, 8]]
        self.eo[[2, 5, 8, 6]] = (self.eo[[6, 2, 5, 8]] + 1) % 2
        self.cp[[3, 2, 5, 4]] = self.cp[[4, 3, 2, 5]]
        self.co[[3, 2, 5, 4]] = self.co[[4, 3, 2, 5]]

        self.co[[2, 4]] = (self.co[[2, 4]] + 1) % 3
        self.co[[3, 5]] = (self.co[[3, 5]] + 2) % 3

    def f_prime(self):
        """Apply F' move to cube state."""

        self.ep[[2, 5, 8, 6]] = self.ep[[5, 8, 6, 2]]
        self.eo[[2, 5, 8, 6]] = (self.eo[[5, 8, 6, 2]] + 1) % 2
        self.cp[[3, 2, 5, 4]] = self.cp[[2, 5, 4, 3]]
        self.co[[3, 2, 5, 4]] = self.co[[2, 5, 4, 3]]

        self.co[[2, 4]] = (self.co[[2, 4]] + 1) % 3
        self.co[[3, 5]] = (self.co[[3, 5]] + 2) % 3

    def f2(self):
        """Apply F2 move to cube state."""

        self.ep[[2, 5, 8, 6]] = self.ep[[8, 6, 2, 5]]
        self.eo[[2, 5, 8, 6]] = self.eo[[8, 6, 2, 5]]
        self.cp[[3, 2, 5, 4]] = self.cp[[5, 4, 3, 2]]
        self.co[[3, 2, 5, 4]] = self.co[[5, 4, 3, 2]]

    def b(self):
        """Apply B move to cube state."""

        self.ep[[0, 7, 10, 4]] = self.ep[[4, 0, 7, 10]]
        self.eo[[0, 7, 10, 4]] = (self.eo[[4, 0, 7, 10]] + 1) % 2
        self.cp[[1, 0, 7, 6]] = self.cp[[6, 1, 0, 7]]
        self.co[[1, 0, 7, 6]] = self.co[[6, 1, 0, 7]]

        self.co[[0, 6]] = (self.co[[0, 6]] + 1) % 3
        self.co[[1, 7]] = (self.co[[1, 7]] + 2) % 3

    def b_prime(self):
        """Apply B' move to cube state."""

        self.ep[[0, 7, 10, 4]] = self.ep[[7, 10, 4, 0]]
        self.eo[[0, 7, 10, 4]] = (self.eo[[7, 10, 4, 0]] + 1) % 2
        self.cp[[1, 0, 7, 6]] = self.cp[[0, 7, 6, 1]]
        self.co[[1, 0, 7, 6]] = self.co[[0, 7, 6, 1]]

        self.co[[0, 6]] = (self.co[[0, 6]] + 1) % 3
        self.co[[1, 7]] = (self.co[[1, 7]] + 2) % 3

    def b2(self):
        """Apply B2 move to cube state."""

        self.ep[[0, 7, 10, 4]] = self.ep[[10, 4, 0, 7]]
        self.eo[[0, 7, 10, 4]] = self.eo[[10, 4, 0, 7]]
        self.cp[[1, 0, 7, 6]] = self.cp[[7, 6, 1, 0]]
        self.co[[1, 0, 7, 6]] = self.co[[7, 6, 1, 0]]

    def ll(self):
        """Apply L move to cube state."""

        self.ep[[3, 6, 11, 7]] = self.ep[[7, 3, 6, 11]]
        self.eo[[3, 6, 11, 7]] = self.eo[[7, 3, 6, 11]]
        self.cp[[0, 3, 4, 7]] = self.cp[[7, 0, 3, 4]]
        self.co[[0, 3, 4, 7]] = self.co[[7, 0, 3, 4]]

        self.co[[0, 4]] = (self.co[[0, 4]] + 2) % 3
        self.co[[3, 7]] = (self.co[[3, 7]] + 1) % 3

    def l_prime(self):
        """Apply L' move to cube state."""

        self.ep[[3, 6, 11, 7]] = self.ep[[6, 11, 7, 3]]
        self.eo[[3, 6, 11, 7]] = self.eo[[6, 11, 7, 3]]
        self.cp[[0, 3, 4, 7]] = self.cp[[3, 4, 7, 0]]
        self.co[[0, 3, 4, 7]] = self.co[[3, 4, 7, 0]]

        self.co[[0, 4]] = (self.co[[0, 4]] + 2) % 3
        self.co[[3, 7]] = (self.co[[3, 7]] + 1) % 3

    def l2(self):
        """Apply L2 move to cube state."""

        self.ep[[3, 6, 11, 7]] = self.ep[[11, 7, 3, 6]]
        self.eo[[3, 6, 11, 7]] = self.eo[[11, 7, 3, 6]]
        self.cp[[0, 3, 4, 7]] = self.cp[[4, 7, 0, 3]]
        self.co[[0, 3, 4, 7]] = self.co[[4, 7, 0, 3]]

    def r(self):
        """Apply R move to cube state."""

        self.ep[[1, 4, 9, 5]] = self.ep[[5, 1, 4, 9]]
        self.eo[[1, 4, 9, 5]] = self.eo[[5, 1, 4, 9]]
        self.cp[[2, 1, 6, 5]] = self.cp[[5, 2, 1, 6]]
        self.co[[2, 1, 6, 5]] = self.co[[5, 2, 1, 6]]

        self.co[[1, 5]] = (self.co[[1, 5]] + 1) % 3
        self.co[[2, 6]] = (self.co[[2, 6]] + 2) % 3

    def r_prime(self):
        """Apply R' move to cube state."""

        self.ep[[1, 4, 9, 5]] = self.ep[[4, 9, 5, 1]]
        self.eo[[1, 4, 9, 5]] = self.eo[[4, 9, 5, 1]]
        self.cp[[2, 1, 6, 5]] = self.cp[[1, 6, 5, 2]]
        self.co[[2, 1, 6, 5]] = self.co[[1, 6, 5, 2]]

        self.co[[1, 5]] = (self.co[[1, 5]] + 1) % 3
        self.co[[2, 6]] = (self.co[[2, 6]] + 2) % 3

    def r2(self):
        """Apply R2 move to cube state."""

        self.ep[[1, 4, 9, 5]] = self.ep[[9, 5, 1, 4]]
        self.eo[[1, 4, 9, 5]] = self.eo[[9, 5, 1, 4]]
        self.cp[[2, 1, 6, 5]] = self.cp[[6, 5, 2, 1]]
        self.co[[2, 1, 6, 5]] = self.co[[6, 5, 2, 1]]


class FasterCubeState():
    """Second iteration cube state model with numpy arrays."""

    def __init__(self):
        """Initialize cube state."""
        self.ep = np.arange(12, dtype=np.int8)
        self.eo = np.zeros(12, dtype=np.int8)
        self.cp = np.arange(8, dtype=np.int8)
        self.co = np.zeros(8, dtype=np.int8)

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

    def apply(self, move):
        """Apply move to cube state."""

        match move:
            case "U": self.u()
            case "U'": self.u_prime()
            case "U2": self.u2()
            case "D": self.d()
            case "D'": self.d_prime()
            case "D2": self.d2()
            case "F": self.f()
            case "F'": self.f_prime()
            case "F2": self.f2()
            case "B": self.b()
            case "B'": self.b_prime()
            case "B2": self.b2()
            case "L": self.ll()
            case "L'": self.l_prime()
            case "L2": self.l2()
            case "R": self.r()
            case "R'": self.r_prime()
            case "R2": self.r2()
            case _: raise ValueError(f"Invalid move {move}")

    def u(self):
        """Apply U move to cube state."""

        self.ep[[0, 1, 2, 3]] = self.ep[[3, 0, 1, 2]]
        self.cp[[0, 1, 2, 3]] = self.cp[[3, 0, 1, 2]]

    def u_prime(self):
        """Apply U' move to cube state."""

        self.ep[[0, 1, 2, 3]] = self.ep[[1, 2, 3, 0]]
        self.cp[[0, 1, 2, 3]] = self.cp[[1, 2, 3, 0]]

    def u2(self):
        """Apply U2 move to cube state."""

        self.ep[[0, 1, 2, 3]] = self.ep[[2, 3, 0, 1]]
        self.cp[[0, 1, 2, 3]] = self.cp[[2, 3, 0, 1]]

    def d(self):
        """Apply D move to cube state."""

        self.ep[[8, 9, 10, 11]] = self.ep[[11, 8, 9, 10]]
        self.cp[[4, 5, 6, 7]] = self.cp[[7, 4, 5, 6]]

    def d_prime(self):
        """Apply D' move to cube state."""

        self.ep[[8, 9, 10, 11]] = self.ep[[9, 10, 11, 8]]
        self.cp[[4, 5, 6, 7]] = self.cp[[5, 6, 7, 4]]

    def d2(self):
        """Apply D2 move to cube state."""

        self.ep[[8, 9, 10, 11]] = self.ep[[10, 11, 8, 9]]
        self.cp[[4, 5, 6, 7]] = self.cp[[6, 7, 4, 5]]

    def f(self):
        """Apply F move to cube state."""

        self.ep[[2, 5, 8, 6]] = self.ep[[6, 2, 5, 8]]
        self.cp[[3, 2, 5, 4]] = self.cp[[4, 3, 2, 5]]

        self.eo[self.ep[[2, 5, 8, 6]]] += 1
        self.co[self.cp[[2, 4]]] += 1
        self.co[self.cp[[3, 5]]] += 2

    def f_prime(self):
        """Apply F' move to cube state."""

        self.ep[[2, 5, 8, 6]] = self.ep[[5, 8, 6, 2]]
        self.cp[[3, 2, 5, 4]] = self.cp[[2, 5, 4, 3]]

        self.eo[self.ep[[2, 5, 8, 6]]] += 1
        self.co[self.cp[[2, 4]]] += 1
        self.co[self.cp[[3, 5]]] += 2

    def f2(self):
        """Apply F2 move to cube state."""

        self.ep[[2, 5, 8, 6]] = self.ep[[8, 6, 2, 5]]
        self.cp[[3, 2, 5, 4]] = self.cp[[5, 4, 3, 2]]

    def b(self):
        """Apply B move to cube state."""

        self.ep[[0, 7, 10, 4]] = self.ep[[4, 0, 7, 10]]
        self.cp[[1, 0, 7, 6]] = self.cp[[6, 1, 0, 7]]

        self.eo[self.ep[[0, 7, 10, 4]]] += 1
        self.co[self.cp[[0, 6]]] += 1
        self.co[self.cp[[1, 7]]] += 2

    def b_prime(self):
        """Apply B' move to cube state."""

        self.ep[[0, 7, 10, 4]] = self.ep[[7, 10, 4, 0]]
        self.cp[[1, 0, 7, 6]] = self.cp[[0, 7, 6, 1]]

        self.eo[self.ep[[0, 7, 10, 4]]] += 1
        self.co[self.cp[[0, 6]]] += 1
        self.co[self.cp[[1, 7]]] += 2

    def b2(self):
        """Apply B2 move to cube state."""

        self.ep[[0, 7, 10, 4]] = self.ep[[10, 4, 0, 7]]
        self.cp[[1, 0, 7, 6]] = self.cp[[7, 6, 1, 0]]

    def ll(self):
        """Apply L move to cube state."""

        self.ep[[3, 6, 11, 7]] = self.ep[[7, 3, 6, 11]]
        self.cp[[0, 3, 4, 7]] = self.cp[[7, 0, 3, 4]]

        self.co[self.cp[[0, 4]]] += 2
        self.co[self.cp[[3, 7]]] += 1

    def l_prime(self):
        """Apply L' move to cube state."""

        self.ep[[3, 6, 11, 7]] = self.ep[[6, 11, 7, 3]]
        self.cp[[0, 3, 4, 7]] = self.cp[[3, 4, 7, 0]]

        self.co[self.cp[[0, 4]]] += 2
        self.co[self.cp[[3, 7]]] += 1

    def l2(self):
        """Apply L2 move to cube state."""

        self.ep[[3, 6, 11, 7]] = self.ep[[11, 7, 3, 6]]
        self.cp[[0, 3, 4, 7]] = self.cp[[4, 7, 0, 3]]

    def r(self):
        """Apply R move to cube state."""

        self.ep[[1, 4, 9, 5]] = self.ep[[5, 1, 4, 9]]
        self.cp[[2, 1, 6, 5]] = self.cp[[5, 2, 1, 6]]

        self.co[self.cp[[1, 5]]] += 1
        self.co[self.cp[[2, 6]]] += 2

    def r_prime(self):
        """Apply R' move to cube state."""

        self.ep[[1, 4, 9, 5]] = self.ep[[4, 9, 5, 1]]
        self.cp[[2, 1, 6, 5]] = self.cp[[1, 6, 5, 2]]

        self.co[self.cp[[1, 5]]] += 1
        self.co[self.cp[[2, 6]]] += 2

    def r2(self):
        """Apply R2 move to cube state."""

        self.ep[[1, 4, 9, 5]] = self.ep[[9, 5, 1, 4]]
        self.cp[[2, 1, 6, 5]] = self.cp[[6, 5, 2, 1]]
