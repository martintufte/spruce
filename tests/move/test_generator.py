from rubiks_cube.move.generator import MoveGenerator
from rubiks_cube.move.generator import simplify


def test_main() -> None:
    gen = MoveGenerator("<(R)R' (),(R'), R RR, R,xLw,R2'F, (R), ((R')R),, R'>")
    simple_gen = simplify(gen)
    control_gen = simplify(simple_gen)

    print("Initial generator:", gen)
    print("Simplyfied generator:", simple_gen)
    assert simple_gen == control_gen, "Simplify function failed!"
