# Code from:
# https://gist.github.com/jacklee1792/45cbcabd9cdaf192f1458e752423af82
# This code is a Python implementation of the slice solver by Jack Lee.
# TODO: Understand this implementation

import argparse
import itertools
import sys


WIDENERS = {
    "U": "E'",
    "U'": "E",
    "D": "E",
    "D'": "E'",
    "U2": "E2",
    "D2": "E2",
}


def detect_axis(seq):
    """
    Remap DR sequence to U/D axis, return functions to map/unmap a sequence.
    """
    is_fb = any(qt in seq for qt in "F F' B B'".split())
    is_lr = any(qt in seq for qt in "L L' R R'".split())
    is_ud = any(qt in seq for qt in "U U' D D'".split())

    count = sum((is_fb, is_lr, is_ud))
    if count > 1:
        print("Error: input sequence has quarter turns on multiple DR axes.")
        sys.exit(0)
    elif count == 0:
        print("Error: input sequence does not contain any quarter turns.")
        sys.exit(0)

    fb2ud = {
        "F": "U",
        "F'": "U'",
        "F2": "U2",
        "B": "D",
        "B'": "D'",
        "B2": "D2",
        "R2": "L2",
        "L2": "R2",
        "D2": "B2",
        "U2": "F2",
    }

    lr2ud = {
        "R": "U",
        "R'": "U'",
        "R2": "U2",
        "L": "D",
        "L'": "D'",
        "L2": "D2",
        "F2": "F2",
        "B2": "B2",
        "U2": "L2",
        "D2": "R2",
    }

    ud2fb = {v: k for k, v in fb2ud.items()} | {"E": "S'", "E'": "S", "E2": "S2"}
    ud2lr = {v: k for k, v in lr2ud.items()} | {"E": "M", "E'": "M'", "E2": "M2"}

    if is_fb:

        def map_func(moves):
            return [fb2ud[move] for move in moves]

        def unmap_func(move):
            return ud2fb[move]

    elif is_lr:

        def map_func(moves):
            return [lr2ud[move] for move in moves]

        def unmap_func(move):
            return ud2lr[move]

    else:

        def map_func(moves):
            assert all(move in "U U' U2 D D' D2 F2 B2 L2 R2".split() for move in moves)
            return moves

        def unmap_func(move):
            return move

    return map_func, unmap_func


def slice_candidates(seq):
    """
    Report the slice cost at each valid slot
    """
    candidates = [{"": 0} for _ in seq]

    i = 0
    for is_ud_chunk, chunk in itertools.groupby(
        seq, lambda move: "U" in move or "D" in move
    ):
        chunk = list(chunk)
        # For continuous sequences of U/D moves, slice at the end
        if is_ud_chunk:
            try:
                (move,) = chunk
            except ValueError:
                print("Slicing for simultaneous DR axis turns is not supported")
                sys.exit(0)

            widener = WIDENERS[move]
            candidates[i] = {"": 0, "E": 1, "E'": 1, "E2": 1} | {widener: 0}
        # For continuous sequences of non-U/D moves, consider slicing between
        # all moves
        else:
            for j, _ in enumerate(chunk[:-1]):
                candidates[i + j] = {"": 0, "E": 2, "E'": 2, "E2": 2}
        i += len(chunk)

    return candidates


def apply(state, moves):
    """
    Return a copy of the state after applying the given moves
    """
    transforms = {
        "R2": {1: 2, 2: 1},
        "L2": {0: 3, 3: 0},
        "F2": {2: 3, 3: 2},
        "B2": {0: 1, 1: 0},
        "E": {0: 3, 3: 2, 2: 1, 1: 0},
        "E'": {0: 1, 1: 2, 2: 3, 3: 0},
        "E2": {0: 2, 2: 0, 1: 3, 3: 1},
    }
    for move in moves:
        tmp = state.copy()
        for from_, to in transforms.get(move, {}).items():
            tmp[to] = state[from_]
        state = tmp

    return state


def get_solutions(state, seq, candidates, budget, balance=0):
    """
    Get the solutions using exactly the given budget
    """
    if budget < 0:
        return []
    if len(candidates) == 0:
        ok = state == [0, 1, 2, 3] and budget == 0 and balance % 4 == 0
        return [[]] if ok else []

    ret = []
    for slice_, cost in candidates[0].items():
        sub_sols = get_solutions(
            state=apply(state, [seq[0], slice_]),
            seq=seq[1:],
            candidates=candidates[1:],
            budget=budget - cost,
            balance=balance + {"": 0, "E": 1, "E2": 2, "E'": 3}[slice_],
        )
        ret.extend([[slice_] + sol for sol in sub_sols])
    return ret


def format_solution(seq, solution, unmap):
    out = []
    for move, slice_ in zip(seq, solution):
        if not slice_:
            out.append(unmap(move))
        elif ("U" in move or "D" in move) and slice_ == WIDENERS[move]:
            out.append(unmap(move) + "[w]")
        else:
            out.append(f"{unmap(move)} [{unmap(slice_)}]")
    return " ".join(out)


def main():
    parser = argparse.ArgumentParser(description="Solve the slice for a DR sequence.")
    parser.add_argument("init_state", help="The starting slice configuration")
    parser.add_argument("sequence", help="The DR sequence to solve by inserting slices")
    parser.add_argument(
        "-n", default=1, type=int, help="The number of solutions to generate"
    )
    parser.add_argument("-M", default=4, type=int, help="Maximum budget for slicing")
    args = parser.parse_args()

    init = args.init_state.split()
    seq = args.sequence.split()

    if not all(move.endswith("2") for move in init):
        print("error: init sequence should only contain double turns")

    # Remap to U/D DR axis
    map_func, unmap_func = detect_axis(seq)

    # Normalize init
    try:
        init = map_func(init)
    except Exception:
        print("Error: invalid init sequence")
        return

    # Normalize seq
    try:
        seq = map_func(seq)
    except Exception:
        print("Error: invalid input sequence")
        return

    # Generate candidates for each slot
    try:
        candidates = slice_candidates(seq)
    except ValueError as e:
        print(f"error: {e}")
        return

    # Find solutions
    state = apply([0, 1, 2, 3], init)
    found = 0
    for budget in range(args.M + 1):
        sols = get_solutions(state, seq, candidates, budget)

        def score(sol):
            locations = [i for i, move in enumerate(sol) if move != ""]
            count = len(locations)
            extent = 0 if locations == [] else locations[-1] - locations[0]
            return count, extent

        sols.sort(key=score)

        for sol in sols:
            found += 1
            print(format_solution(seq, sol, unmap_func), f"(+{budget})")
            if found >= args.n:
                return


if __name__ == "__main__":
    main()
