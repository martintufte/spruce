from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.move.steps import MoveSteps
from rubiks_cube.parsing import parse_steps


def test_parse_steps_returns_move_steps() -> None:
    parsed = parse_steps("R U\nF2")

    assert isinstance(parsed, MoveSteps)
    assert parsed == MoveSteps.from_strings(["R U", "F2"])


def test_parse_steps_empty_input() -> None:
    parsed = parse_steps("")
    assert parsed == MoveSteps()


def test_parse_steps_skeleton_mode_returns_single_step() -> None:
    parsed = parse_steps("-> R U R' U'")
    assert parsed == MoveSteps([MoveSequence.from_str("R U R' U'")])
