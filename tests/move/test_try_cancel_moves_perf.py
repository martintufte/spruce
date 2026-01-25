import time

from rubiks_cube.meta.move import MoveMeta
from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.move.sequence import try_cancel_moves
from rubiks_cube.move.utils import is_rotation
from rubiks_cube.representation.permutation import create_permutations


def _naive_cancel(sequence: MoveSequence, cube_size: int) -> None:
    permutations = create_permutations(cube_size=cube_size)
    legal_moves = {move for move in permutations if move != "I" and not is_rotation(move)}
    move_by_perm_bytes = {permutations[move].tobytes(): move for move in legal_moves}
    identity_bytes = permutations["I"].tobytes()

    output: list[str] = []
    segment: list[str] = []

    def reduce_segment(moves: list[str]) -> list[str]:
        stack: list[str] = []
        for move in moves:
            stack.append(move)
            if move not in legal_moves:
                continue
            while True:
                if not stack:
                    break
                current = stack[-1]
                if current not in legal_moves:
                    break
                combined_pos = None
                combined_move = None
                for pos in range(len(stack) - 2, -1, -1):
                    previous = stack[pos]
                    if previous not in legal_moves:
                        break
                    can_commute = True
                    for between in stack[pos + 1 : -1]:
                        perm_prev = permutations[previous]
                        perm_between = permutations[between]
                        if not (perm_prev[perm_between] == perm_between[perm_prev]).all():
                            can_commute = False
                            break
                    if not can_commute:
                        continue
                    composed = permutations[previous][permutations[current]]
                    composed_bytes = composed.tobytes()
                    if composed_bytes == identity_bytes:
                        combined_pos = pos
                        combined_move = ""
                        break
                    combined = move_by_perm_bytes.get(composed_bytes)
                    if combined is not None:
                        combined_pos = pos
                        combined_move = combined
                        break
                if combined_pos is None:
                    break
                stack.pop()
                del stack[combined_pos]
                if combined_move:
                    stack.append(combined_move)
        return stack

    for move in sequence:
        if is_rotation(move):
            if segment:
                output.extend(reduce_segment(segment))
                segment = []
            output.append(move)
        else:
            segment.append(move)

    if segment:
        output.extend(reduce_segment(segment))

    sequence.moves = output


def test_try_cancel_moves_is_faster_than_naive() -> None:
    cube_size = 3
    base = "L F Rw2 Rw2 F' L Rw L' R Rw "
    seq = MoveSequence.from_str(base) * 200

    MoveMeta.from_cube_size.cache_clear()
    move_meta = MoveMeta.from_cube_size(cube_size)

    # Cancel once to cache the table
    try_cancel_moves(seq, move_meta)

    start = time.perf_counter()
    for _ in range(100):
        try_cancel_moves(seq, move_meta)
    cached_time = time.perf_counter() - start

    start = time.perf_counter()
    for _ in range(100):
        _naive_cancel(seq, cube_size=cube_size)
    naive_time = time.perf_counter() - start

    assert naive_time / cached_time >= 10
