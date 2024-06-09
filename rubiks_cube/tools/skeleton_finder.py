import numpy as np

from rubiks_cube.permutation import apply_moves
from rubiks_cube.permutation.tracing import count_solved
from rubiks_cube.permutation.tracing import count_similar
from rubiks_cube.permutation.tracing import is_solved
from rubiks_cube.utils.sequence import Sequence


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
