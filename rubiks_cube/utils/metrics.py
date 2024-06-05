import re

from rubiks_cube.utils import Metric


def count_length(moves: list[str], metric: Metric = Metric.HTM) -> int:
    """
    Count the length of a sequence of moves.
    ETM = Execution Turn Metric
    HTM = Half Turn Metric
    STM = Slice Turn Metric
    QTM = Quarter Turn Metric
    """

    count = len(moves) - sum(move.strip() == "" for move in moves)
    slices = sum(bool(re.search('[MES]', move)) for move in moves)
    rotations = sum(bool(re.search('[xyz]', move)) for move in moves)

    if metric is Metric.ETM:
        return count
    elif metric is Metric.HTM:
        return count + slices - rotations
    elif metric is Metric.STM:
        return count - rotations
    elif metric is Metric.QTM:
        d_count = sum(bool(re.search('[2]', move)) for move in moves)
        d_slices = sum(bool(re.search('[MES]2', move)) for move in moves)
        d_rotations = sum(bool(re.search('[xyz]2', move)) for move in moves)
        return count + slices - rotations + d_count + d_slices - d_rotations


def main() -> None:
    for metric in [Metric.ETM, Metric.HTM, Metric.STM, Metric.QTM]:
        print(f"\n{metric}:")
        for moves in [
            [" "],
            ["R"], ["R2"], ["R'"], ["(R)"], ["(R2)"], ["(R')"],
            ["M"], ["M2"], ["M'"], ["(M)"], ["(M2)"], ["(M')"],
            ["x"], ["x2"], ["x'"], ["(x)"], ["(x2)"], ["(x')"],
            ["Rw"], ["Rw2"], ["Rw'"], ["(Rw)"], ["(Rw2)"], ["(Rw')"]
        ]:
            print(moves, count_length(moves, metric))


if __name__ == "__main__":
    main()
