import time
import numpy as np

from cube_state import CubeState as CubeState
from int_cube_state import CubeState as IntCubeState
from numba_cube_state import CubeState as NumbaCubeState


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


def integer_to_list(n, base=2, length=12, infer=True):
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


if __name__ == "__main__":

    ''' Test 1 for seeing that the cube state is working
    scramble = "U U' U2 D D' D2 F F' F2 B B' B2 L L' L2 R R' R2"
    for move in scramble.split():
        print("\n" + move)
        state = CubeState()
        state.apply(move)
        print(state)
    '''

    ''' Test 2 for seeing that the cube state is working
    scramble = "R' U' F U' F' U F L D' B' D F'\
        L2 F' U2 B' R2 B R2 U2 B2 L2 D R' U' F"
    state = CubeState()
    for move in scramble.split():
        state.apply(move)
        print(state)
    '''

    '''
    # Test 3 for seeing that the cube state is working
    # set seed
    times = []
    seeds = [0, 1, 2, 3, 4]
    move_list = ["U", "U'", "U2", "D", "D'", "D2", "F", "F'", "F2",
                 "B", "B'", "B2", "L", "L'", "L2", "R", "R'", "R2"]

    for seed in seeds:
        np.random.seed(seed)
        scramble = list(np.random.choice(move_list, 100000))
        state = CubeState()

        # Time the scramble
        time_start = time.time()
        for move in scramble:
            state.apply(move)
        time_end = time.time()
        times.append(time_end - time_start)

    # Print the average and standard deviation
    print(np.mean(times))  # 2.073 seconds
    print(np.std(times))   # 0.012 seconds

    '''
    # Test 4 for seeing that the cube state is working
    times = []
    seeds = [6, 7, 8, 9, 10]
    move_list = ["U", "U'", "U2", "D", "D'", "D2", "F", "F'", "F2",
                 "B", "B'", "B2", "L", "L'", "L2", "R", "R'", "R2"]
    move_list_dr = ["U", "U'", "U2", "D", "D'", "D2", "R2", "F2", "L2", "B2"]

    # allow the numba to compile before timing
    state = IntCubeState()
    for move in "R' U' F U' F' U F L2 D R' U' F".split():
        state.apply(move)

    for seed in seeds:
        np.random.seed(seed)
        scramble = list(np.random.choice(move_list, 1000000))
        # state = CubeState()  # 2.073 sec
        # state = FasterCubeState()  # 1.303 sec (37.22 % faster)
        # state = NumbaCubeState()  # 0.284 sec (86.32 % faster)
        # with cache=True: 0.103 sec (95.02 % faster)
        # (7% faster with dictionary instead of match)
        state = NumbaCubeState()

        # Time the scramble
        time_start = time.perf_counter()
        for move in scramble:
            state.apply(move)
        time_end = time.perf_counter()
        times.append(time_end - time_start)

    # Print the average and standard deviation
    print(np.mean(times))  # 2.073 sec -> 1.303 sec
    print(np.std(times))   # 0.012 sec -> 0.012 sec

    # Check that the cube state is working for FasterCubeState
    scramble = "R' U' F U' F' U F L2 D R' U' F"
    ref_state = CubeState()
    state = IntCubeState()
    for move in scramble.split():
        ref_state.apply(move)
        state.apply(move)
    print(ref_state)
    print(state)

    '''
    move_list = "U U' U2 D D' D2 F F' F2 B B' B2 L L' L2 R R' R2".split()

    # Create tables for IntCubeState
    eofb = np.zeros((18, 2048), dtype=np.uint8)
    coud = np.zeros((18, 2187), dtype=np.uint8)

    state = NumbaCubeState()
    for i in range(2048):
        # apply moves
        for e, move in enumerate(move_list):
            state.set_eo(integer_to_list(i, base=2, length=12))
            state.apply(move)
            eofb[e, i] = list_to_integer(state.get_eo(), base=2)

    print("EOFB:", eofb[6, :])

    for i in range(2187):
        # apply moves
        for e, move in enumerate(move_list):
            state.set_co(integer_to_list(i, base=3, length=8))
            state.apply(move)
            coud[e, i] = list_to_integer(state.get_co(), base=3)

    print("COUD:", coud[6, :])

    # Save tables
    np.save("tables/eofb.npy", eofb)
    np.save("tables/coud.npy", coud)
    ref_state = CubeState()
    state = IntCubeState()
    for move in "R' U' F".split():
        ref_state.apply(move)
        state.apply(move)
    print(ref_state)
    print(state)
    '''
