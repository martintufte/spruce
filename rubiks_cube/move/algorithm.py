from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any

from numpy import array_equal

from rubiks_cube.representation import get_rubiks_cube_state

if TYPE_CHECKING:
    from rubiks_cube.configuration.types import CubeRange
    from rubiks_cube.move.sequence import MoveSequence


class MoveAlgorithm:
    def __init__(
        self,
        name: str,
        sequence: MoveSequence,
        cube_range: CubeRange = (None, None),
    ) -> None:
        """Initialize the move algorithm.

        Args:
            name (str): Name of the algorithm.
            sequence (MoveSequence): The sequence of moves.
            cube_range (CubeRange, optional): Range of cube size. Defaults to (None, None).
        """
        assert len(name) >= 2 and " " not in name and name.isascii(), "Invalid algorithm name!"
        assert cube_range[0] is None or cube_range[0] >= 1, "Cube size too small!"
        self.name = name
        self.sequence = sequence
        self.cube_range = cube_range

    def __str__(self) -> str:
        if not self.sequence:
            return f"MoveAlgorithm('{self.name}': )"
        return f"MoveAlgorithm('{self.name}': {self.sequence!s})"

    def __repr__(self) -> str:
        return f"MoveAlgorithm('{self.name}', {self.sequence!s})"

    def __len__(self) -> int:
        return len(self.sequence)

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, MoveAlgorithm):
            return array_equal(
                get_rubiks_cube_state(self.sequence), get_rubiks_cube_state(other.sequence)
            )
        return False

    def __ne__(self, other: Any) -> bool:
        return not self == other

    def __lt__(self, other: Any) -> bool:
        if isinstance(other, MoveAlgorithm):
            return len(self) < len(other)
        return False

    def __le__(self, other: Any) -> bool:
        if isinstance(other, MoveAlgorithm):
            return len(self) <= len(other)
        return False

    def __gt__(self, other: Any) -> bool:
        if isinstance(other, MoveAlgorithm):
            return len(self) > len(other)
        return False

    def __ge__(self, other: Any) -> bool:
        if isinstance(other, MoveAlgorithm):
            return len(self) >= len(other)
        return False
