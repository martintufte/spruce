from rubiks_cube.configuration.enumeration import Metric
from rubiks_cube.utils.metrics import count_length


def test_main() -> None:
    for metric in [Metric.ETM, Metric.HTM, Metric.STM, Metric.QTM]:
        print(f"\n{metric}:")
    for moves in [
        [" "],
        ["R"],
        ["R2"],
        ["R'"],
        ["(R)"],
        ["(R2)"],
        ["(R')"],
        ["M"],
        ["M2"],
        ["M'"],
        ["(M)"],
        ["(M2)"],
        ["(M')"],
        ["x"],
        ["x2"],
        ["x'"],
        ["(x)"],
        ["(x2)"],
        ["(x')"],
        ["Rw"],
        ["Rw2"],
        ["Rw'"],
        ["(Rw)"],
        ["(Rw2)"],
        ["(Rw')"],
    ]:
        print(moves, count_length(moves, metric))
