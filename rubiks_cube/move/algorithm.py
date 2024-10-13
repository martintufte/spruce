from __future__ import annotations

from typing import Any

from numpy import array_equal

from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.state import get_rubiks_cube_state


class MoveAlgorithm:
    """Rubiks cube move algorithm to represent a named sequence of moves."""

    def __init__(
        self,
        name: str,
        sequence: MoveSequence | str | list[str] | None = None,
        cube_range: tuple[int | None, int | None] = (None, None),
    ) -> None:
        """Initialize the move algorithm.

        Args:
            name (str): Name of the algorithm.
            sequence (MoveSequence | str | list[str] | None): The sequence of moves.
            cube_size (tuple[int | None, int | None], optional):
                Lower and upper band for which cubes sizes the the algorithm is intended for.
                Defaults to (None, None).
        """
        assert len(name) >= 2 and " " not in name and name.isascii(), "Invalid algorithm name!"
        assert cube_range[0] is None or cube_range[0] >= 1, "Cube size too small!"
        self.name = name
        self.sequence = sequence if isinstance(sequence, MoveSequence) else MoveSequence(sequence)
        self.cube_range = cube_range

    def __str__(self) -> str:
        if not self.sequence:
            return f"MoveAlgorithm('{self.name}': )"
        return f"MoveAlgorithm('{self.name}': {str(self.sequence)})"

    def __repr__(self) -> str:
        return f"MoveAlgorithm('{self.name}', {str(self.sequence)})"

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
