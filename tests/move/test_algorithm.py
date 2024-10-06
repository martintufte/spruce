from rubiks_cube.move.algorithm import MoveAlgorithm
from rubiks_cube.move.sequence import MoveSequence


def test_main() -> None:
    alg = MoveAlgorithm("sune", MoveSequence("R U R' U R U2 R'"), cube_range=(3, None))
    print(alg)
