from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any

from attrs import define
from attrs import field
from attrs import validators

from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.move.sequence import cleanup

if TYPE_CHECKING:
    from rubiks_cube.move.meta import MoveMeta


@define(eq=False, repr=False)
class MoveGenerator:
    generator: set[MoveSequence] = field(
        factory=set,
        validator=validators.deep_iterable(
            member_validator=validators.instance_of(MoveSequence),
            iterable_validator=validators.instance_of(set),
        ),
    )

    @classmethod
    def from_str(cls, generator: str) -> MoveGenerator:
        generator = generator.strip()
        if not (generator.startswith("<") and generator.endswith(">")):
            raise ValueError("Invalid move generator format!")
        sequences = generator[1:-1].split(",")
        return cls({MoveSequence.from_str(seq) for seq in sequences})

    def __str__(self) -> str:
        if not self.generator:
            return "<>"
        return "<" + ", ".join(sorted([str(seq) for seq in self.generator], key=len)) + ">"

    def __repr__(self) -> str:
        if not self.generator:
            return "MoveGenerator()"
        return f'MoveGenerator.from_str("{self!s}")'

    def __len__(self) -> int:
        return len(self.generator)

    def __add__(self, other: MoveGenerator | set[MoveSequence]) -> MoveGenerator:
        if isinstance(other, MoveGenerator):
            return MoveGenerator(self.generator | other.generator)
        if isinstance(other, set):
            return MoveGenerator(self.generator | other)
        return NotImplemented

    def __radd__(self, other: MoveGenerator | set[MoveSequence]) -> MoveGenerator:
        if isinstance(other, MoveGenerator):
            return MoveGenerator(other.generator | self.generator)
        if isinstance(other, set):
            return MoveGenerator(other | self.generator)
        return NotImplemented

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, MoveGenerator):
            return self.generator == other.generator
        return False

    def __ne__(self, other: Any) -> bool:
        if isinstance(other, MoveGenerator):
            return self.generator != other.generator
        return True

    def __iter__(self) -> Any:
        for sequence in self.generator:
            yield sequence

    def __contains__(self, item: str) -> bool:
        return item in self.generator

    def __bool__(self) -> bool:
        return bool(self.generator)

    def __copy__(self) -> MoveGenerator:
        return MoveGenerator(generator=self.generator.copy())

    def __lt__(self, other: MoveGenerator | list[str]) -> bool:
        return len(self) < len(other)

    def __le__(self, other: MoveGenerator | list[str]) -> bool:
        return len(self) <= len(other)

    def __gt__(self, other: MoveGenerator | list[str]) -> bool:
        return len(self) > len(other)

    def __ge__(self, other: MoveGenerator | list[str]) -> bool:
        return len(self) >= len(other)


def cleanup_all(generator: MoveGenerator, move_meta: MoveMeta) -> MoveGenerator:
    """Cleanup all sequences in a move generator.

    Args:
        generator (MoveGenerator): Move generator.
        move_meta (MoveMeta): Move meta configuration.

    Returns:
        MoveGenerator: Cleaned move generator.
    """
    return MoveGenerator({cleanup(seq, move_meta) for seq in generator})


def remove_empty(generator: MoveGenerator) -> MoveGenerator:
    """Remove empty sequences from a move generator.

    Args:
        generator (MoveGenerator): Move generator.

    Returns:
        MoveGenerator: Move generator without empty sequences.
    """
    return MoveGenerator({seq for seq in generator if seq})


def simplify(generator: MoveGenerator, move_meta: MoveMeta) -> MoveGenerator:
    """Simplify a move generator.

    Steps:
    - Cleanup all sequences in the generator
    - Remove empty sequences
    - (Remove sequences that are spanned by other sequences)

    Args:
        generator (MoveGenerator): Move generator.
        move_meta (MoveMeta): Move meta configuration.

    Returns:
        MoveGenerator: Simplified move generator.
    """
    generator = cleanup_all(generator, move_meta)
    generator = remove_empty(generator)

    return generator
