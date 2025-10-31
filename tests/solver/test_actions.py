from typing import TYPE_CHECKING

import pytest

from rubiks_cube.configuration import DEFAULT_GENERATOR
from rubiks_cube.move.algorithm import MoveAlgorithm
from rubiks_cube.move.generator import MoveGenerator
from rubiks_cube.solver.actions import get_actions

if TYPE_CHECKING:
    from rubiks_cube.move.sequence import MoveSequence


def test_get_actions_empty_set() -> None:
    """Test get actions from empty set."""
    cube_size = 3
    sequence_set: set[MoveSequence] = set()
    generator = MoveGenerator(sequence_set)
    actions = get_actions(generator=generator, cube_size=cube_size)
    assert len(actions) == 0


def test_get_actions_empty_generator() -> None:
    """Test get empty move sequence results in identity."""
    cube_size = 3
    generator = MoveGenerator("<>")
    actions = get_actions(generator=generator, cube_size=cube_size)
    assert len(actions) == 1


def test_get_actions_standard_moves() -> None:
    """Test get standard moves actions."""
    cube_size = 3
    generator = MoveGenerator(DEFAULT_GENERATOR)
    actions = get_actions(generator=generator, expand_generator=False, cube_size=cube_size)
    assert len(actions) == 6

    actions_expanded = get_actions(generator=generator, cube_size=cube_size)
    assert len(actions_expanded) == 18


def test_get_actions_R() -> None:
    """Test get standard moves actions with no expanding."""
    cube_size = 3
    generator = MoveGenerator("<R>")
    actions = get_actions(generator=generator, cube_size=cube_size)
    assert len(actions) == 3


def test_get_actions_R2() -> None:
    """Test get standard moves actions with no expanding."""
    cube_size = 3
    generator = MoveGenerator("<R2>")
    actions = get_actions(generator=generator, cube_size=cube_size)
    assert len(actions) == 1


def test_get_actions_duplicate() -> None:
    """Test get actions from duplicate sequences."""
    cube_size = 3
    generator = MoveGenerator("<R, R, R>")
    actions = get_actions(generator=generator, expand_generator=False, cube_size=cube_size)
    assert len(actions) == 1


def test_get_actions_from_algorithms() -> None:
    """Test get actions from algorithms."""
    algorithms = [
        MoveAlgorithm(name="sexy", sequence="R U R' U'", cube_range=(None, None)),
        MoveAlgorithm(name="sledge", sequence="R' F R F'", cube_range=(None, None)),
    ]
    cube_size = 3
    actions = get_actions(algorithms=algorithms, expand_generator=False, cube_size=cube_size)
    assert len(actions) == 2
    assert "sexy" in actions
    assert "sledge" in actions


def test_get_actions_from_algorithms_not_in_range() -> None:
    """Test get actions from algorithm not in cube range."""
    algorithms = [
        MoveAlgorithm(
            name="oll-parity",
            sequence="Rw U2 x Rw U2 Rw U2 Rw' U2 Lw U2 Rw' U2 Rw U2 Rw' U2 Rw'",
            cube_range=(4, 4),
        ),
    ]
    cube_size = 3
    with pytest.raises(AssertionError):
        get_actions(algorithms=algorithms, expand_generator=False, cube_size=cube_size)
