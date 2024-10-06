from rubiks_cube.configuration.enumeration import State
from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.state.tag.patterns import get_cubexes


def test_main() -> None:
    cube_size = 3
    cubexes = get_cubexes(cube_size=cube_size)
    sequence = MoveSequence("U")

    print(f'\nMoveSequence "{sequence}" tagged with {len(cubexes)} tags:\n')
    for tag, cbx in sorted(cubexes.items()):
        print(f"{tag} ({len(cbx)}):", cbx.match(sequence, cube_size=cube_size))
    print()

    print("Missing tags:")
    for state in State:
        if state.value not in cubexes:
            print(f"{state.value}")

    print("\nMatch specific pattern:")
    print(cubexes["f2l-layer"].match(sequence, cube_size=cube_size))
