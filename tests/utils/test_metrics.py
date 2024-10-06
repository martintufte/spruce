from rubiks_cube.configuration.enumeration import Metric
from rubiks_cube.utils.metrics import count_length


def test_count_length_is_int() -> None:
    for metric in [Metric.ETM, Metric.HTM, Metric.STM, Metric.QTM]:
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
            assert isinstance(count_length(moves, metric), int)
