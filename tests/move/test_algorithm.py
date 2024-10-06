from rubiks_cube.move.algorithm import MoveAlgorithm
from rubiks_cube.move.sequence import MoveSequence


def test_main() -> None:
    alg = MoveAlgorithm("sune", MoveSequence("R U R' U R U2 R'"), cube_range=(3, None))
    assert alg.name == "sune"
    assert alg.sequence == MoveSequence("R U R' U R U2 R'")
    assert alg.cube_range == (3, None)
