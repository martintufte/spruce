from rubiks_cube.utils import Metric


def count_length(
    input_str: str, count_rotations=False, metric: Metric = Metric.HTM
):
    """
    Count the length of a sequence.
    HTM = Half Turn Metric
    STM = Slice Turn Metric
    QTM = Quarter Turn Metric
    """

    n_rotations = sum(1 for char in input_str if char in "xyz")
    n_slices = sum(1 for char in input_str if char in "MES")
    n_double_moves = sum(1 for char in input_str if char in "2")
    n_moves = len(input_str.split())

    if not count_rotations:
        n_moves -= n_rotations

    if metric is Metric.HTM:
        return n_moves + n_slices
    elif metric is Metric.STM:
        return n_moves
    elif metric is Metric.QTM:
        return n_moves + n_double_moves
