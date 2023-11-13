import numpy as np

from utils.permutations import (
    is_solved,
    count_solved,
    count_similar
)
from utils.cube import apply_moves


def generate_cube_states(init_perm, depth=3):
    all_states = {}

    return all_states


if __name__ == "__main__":
    SOLVED = np.arange(54)

    p = apply_moves(SOLVED, "R U R' U' R U R' U' R U R' U'")
    q = apply_moves(SOLVED, "R' U2 R")

    print("Solved:", is_solved(p))
    print("Number of solved pieces:", count_solved(p))
    print("Number of similar pieces:", count_similar(p, q))
