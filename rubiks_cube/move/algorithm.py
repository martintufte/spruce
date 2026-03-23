from __future__ import annotations

from typing import Any
from typing import Final
from typing import Self

from attrs import frozen

from rubiks_cube.move.sequence import MoveSequence

KNOWN_ALGORITHMS: Final[dict[str, MoveSequence]] = {
    ":t-perm:": MoveSequence.from_str("R U R' U' R' F R2 U' R' U' R U R' F'"),
    ":jb-perm:": MoveSequence.from_str("R U R' F' R U R' U' R' F R2 U' R'"),
    ":sexy:": MoveSequence.from_str("R U R' U'"),
    ":sledge:": MoveSequence.from_str("R' F R F'"),
    ":oll-parity:": MoveSequence.from_str(
        "Rw U2 x Rw U2 Rw U2 Rw' U2 Lw U2 Rw' U2 Rw U2 Rw' U2 Rw'"
    ),
}


@frozen
class MoveAlgorithm:
    name: str
    sequence: MoveSequence

    @classmethod
    def from_str(cls, string: str) -> Self:
        if string not in KNOWN_ALGORITHMS:
            raise ValueError("Unknown algorithm name provided!")
        return cls(name=string, sequence=KNOWN_ALGORITHMS[string])

    def __attrs_post_init__(self) -> None:
        if " " in self.name or not self.name.isascii():
            raise ValueError(f"Algorithm name got unsupported characters: {self.name!s}")

    def __str__(self) -> str:
        return f":{self.name}:"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}('{self.name}', {self.sequence!s})"

    def __ne__(self, other: Any) -> bool:
        return not self == other

    def __len__(self) -> int:
        return len(self.sequence)
