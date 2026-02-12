from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any

from attrs import frozen
from numpy import array_equal

from rubiks_cube.representation import get_rubiks_cube_permutation

if TYPE_CHECKING:
    from rubiks_cube.configuration.types import CubeRange
    from rubiks_cube.move.sequence import MoveSequence


@frozen
class MoveAlgorithm:
    name: str
    sequence: MoveSequence
    cube_range: CubeRange = (None, None)

    def __attrs_post_init__(self) -> None:
        assert (
            len(self.name) >= 2 and " " not in self.name and self.name.isascii()
        ), "Invalid algorithm name!"
        assert self.cube_range[0] is None or self.cube_range[0] >= 1, "Cube size too small!"

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
                get_rubiks_cube_permutation(self.sequence),
                get_rubiks_cube_permutation(other.sequence),
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
