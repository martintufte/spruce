import numpy as np

from utils.permutations import apply_moves
from utils.permutations import count_solved
from utils.permutations import count_similar
from utils.permutations import is_solved
from utils.sequence import Sequence


def generate_cube_states(init_perm, depth=3):
    all_states = {}

    return all_states


if __name__ == "__main__":
    SOLVED = np.arange(54)

    p = apply_moves(SOLVED, Sequence("R U R' U' R U R' U' R U R' U'"))
    q = apply_moves(SOLVED, Sequence("R' U2 R"))

    print("Solved:", is_solved(p))
    print("Number of solved pieces:", count_solved(p))
    print("Number of similar pieces:", count_similar(p, q))
