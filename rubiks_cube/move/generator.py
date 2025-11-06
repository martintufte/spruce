from __future__ import annotations

from typing import Any

from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.move.sequence import cleanup


class MoveGenerator:
    generator: set[MoveSequence]

    def __init__(self, generator: str | set[MoveSequence] | None = None) -> None:
        """Initialize the move generator.

        Args:
            generator (str | set[MoveSequence] | None, optional):
                String of format "<seq1, seq2, ...>" or set of move sequences. Defaults to None.

        Raises:
            ValueError: Invalid move generator format!
        """
        if generator is None:
            self.generator = set()
        elif isinstance(generator, str):
            generator = generator.strip()
            if not (generator.startswith("<") and generator.endswith(">")):
                raise ValueError("Invalid move generator format!")
            sequences = generator[1:-1].split(",")
            self.generator = {MoveSequence(seq) for seq in sequences}
        else:
            self.generator = generator

    def __str__(self) -> str:
        if not self.generator:
            return "<>"
        return "<" + ", ".join(sorted([str(seq) for seq in self.generator], key=len)) + ">"

    def __repr__(self) -> str:
        return f'MoveGenerator("{self!s}")'

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


def cleanup_all(generator: MoveGenerator) -> MoveGenerator:
    """Cleanup all sequences in a move generator.

    Args:
        generator (MoveGenerator): Move generator.

    Returns:
        MoveGenerator: Cleaned move generator.
    """
    return MoveGenerator({cleanup(seq) for seq in generator})


def remove_empty(generator: MoveGenerator) -> MoveGenerator:
    """Remove empty sequences from a move generator.

    Args:
        generator (MoveGenerator): Move generator.

    Returns:
        MoveGenerator: Move generator without empty sequences.
    """
    return MoveGenerator({seq for seq in generator if seq})


def remove_inversed(generator: MoveGenerator) -> MoveGenerator:
    """Remove duplicate sequences that are inverses of each other.

    Args:
        generator (MoveGenerator): Move generator.

    Returns:
        MoveGenerator: Move generator without inverse duplicates.
    """
    new_generator = set()
    for seq in generator:
        clean_inv_seq = cleanup(~seq)
        if clean_inv_seq not in new_generator and seq not in new_generator:
            # Use the sequence with the shortest representation
            if len(str(seq)) <= len(str(clean_inv_seq)):
                new_generator.add(seq)
            else:
                new_generator.add(clean_inv_seq)

    return MoveGenerator(new_generator)


def simplify(generator: MoveGenerator) -> MoveGenerator:
    """Simplify a move generator.

    Steps:
    - Cleanup all sequences in the generator
    - Remove empty sequences
    - Remove sequences that are inverse of each other
    - (Remove sequences that are spanned by other sequences)

    Args:
        generator (MoveGenerator): Move generator.

    Returns:
        MoveGenerator: Simplified move generator.
    """
    generator = cleanup_all(generator)
    generator = remove_empty(generator)
    generator = remove_inversed(generator)

    return generator
