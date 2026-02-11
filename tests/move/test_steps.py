import pytest

from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.move.steps import MoveSteps


class TestMoveSteps:
    def test_empty_move_steps_properties(self) -> None:
        steps = MoveSteps()
        assert len(steps) == 0
        assert str(steps) == "None"
        assert not steps
        assert steps.to_sequence() == MoveSequence()

    def test_from_strings_and_iteration(self) -> None:
        steps = MoveSteps.from_strings(["R U", "R' U'"])
        assert len(steps) == 2
        assert steps[0] == MoveSequence.from_str("R U")
        assert steps[1] == MoveSequence.from_str("R' U'")
        assert list(steps) == [MoveSequence.from_str("R U"), MoveSequence.from_str("R' U'")]

    def test_index_and_slice(self) -> None:
        steps = MoveSteps.from_strings(["R", "U", "F"])
        assert steps[0] == MoveSequence.from_str("R")
        assert list(steps[1:]) == [MoveSequence.from_str("U"), MoveSequence.from_str("F")]

    def test_addition_with_move_steps(self) -> None:
        left = MoveSteps.from_strings(["R U"])
        right = MoveSteps.from_strings(["R' U'"])
        assert left + right == MoveSteps.from_strings(["R U", "R' U'"])

    def test_addition_with_sequence(self) -> None:
        left = MoveSteps.from_strings(["R U"])
        right = [MoveSequence.from_str("F"), MoveSequence.from_str("F'")]
        assert left + right == MoveSteps.from_strings(["R U", "F", "F'"])

    def test_to_sequence(self) -> None:
        steps = MoveSteps.from_strings(["R U", "R' U'"])
        assert steps.to_sequence() == MoveSequence.from_str("R U R' U'")

    def test_without_empty(self) -> None:
        steps = MoveSteps([MoveSequence.from_str("R"), MoveSequence(), MoveSequence.from_str("U")])
        assert steps.without_empty() == MoveSteps.from_strings(["R", "U"])

    def test_with_step_returns_new_instance(self) -> None:
        steps = MoveSteps.from_strings(["R"])
        updated = steps.with_step(MoveSequence.from_str("U"))
        assert steps == MoveSteps.from_strings(["R"])
        assert updated == MoveSteps.from_strings(["R", "U"])

    def test_invalid_step_type_raises(self) -> None:
        with pytest.raises(TypeError):
            MoveSteps(steps=["R"])  # type: ignore[list-item]

    def test_apply_local_update_not_implemented(self) -> None:
        steps = MoveSteps.from_strings(["R U"])
        with pytest.raises(NotImplementedError):
            steps.apply_local_update(0, "R U R'")

    def test_resolve_subsets_not_implemented(self) -> None:
        steps = MoveSteps.from_strings(["R U"])
        with pytest.raises(NotImplementedError):
            steps.resolve_subsets()
