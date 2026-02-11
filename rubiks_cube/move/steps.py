from __future__ import annotations

from collections.abc import Iterator
from collections.abc import Sequence
from typing import Any
from typing import overload

from attrs import define
from attrs import field
from attrs import validators

from rubiks_cube.move.sequence import MoveSequence


@define(eq=False, repr=False)
class MoveSteps(Sequence[MoveSequence]):
    """Container for step-wise move sequences.

    This class is a lightweight scaffold for upcoming step parsing work.
    It wraps a list of :class:`MoveSequence` and keeps common operations in one place.
    """

    steps: list[MoveSequence] = field(
        factory=list,
        validator=validators.deep_iterable(
            member_validator=validators.instance_of(MoveSequence),
            iterable_validator=validators.instance_of(list),
        ),
    )

    @classmethod
    def from_strings(cls, steps: Sequence[str]) -> MoveSteps:
        """Build from raw step strings."""
        return cls([MoveSequence.from_str(step) for step in steps])

    def __str__(self) -> str:
        if len(self.steps) == 0:
            return "None"
        return "\n".join(str(step) for step in self.steps)

    def __repr__(self) -> str:
        if len(self.steps) == 0:
            return f"{self.__class__.__name__}()"
        return f"{self.__class__.__name__}({self.steps!r})"

    def __len__(self) -> int:
        return len(self.steps)

    @overload
    def __getitem__(self, index: int) -> MoveSequence: ...

    @overload
    def __getitem__(self, index: slice) -> Sequence[MoveSequence]: ...

    def __getitem__(self, index: int | slice) -> MoveSequence | Sequence[MoveSequence]:
        if isinstance(index, (slice, int)):
            return self.steps[index]
        raise IndexError("Invalid index provided for MoveSteps.")

    def __iter__(self) -> Iterator[MoveSequence]:
        for step in self.steps:
            yield step

    def __bool__(self) -> bool:
        return bool(self.steps)

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, MoveSteps):
            return self.steps == other.steps
        return False

    def __add__(self, other: MoveSteps | Sequence[MoveSequence]) -> MoveSteps:
        if isinstance(other, MoveSteps):
            return MoveSteps(self.steps + other.steps)
        if isinstance(other, Sequence):
            return MoveSteps(self.steps + list(other))
        return NotImplemented

    def to_sequence(self) -> MoveSequence:
        """Combine all steps into one move sequence."""
        return sum(self.steps, start=MoveSequence())

    def without_empty(self) -> MoveSteps:
        """Return only non-empty steps."""
        return MoveSteps([step for step in self.steps if len(step) > 0])

    def with_step(self, step: MoveSequence) -> MoveSteps:
        """Append a new step and return a new instance."""
        return MoveSteps([*self.steps, step])

    def apply_local_update(self, _line_number: int, _new_line: str) -> MoveSteps:
        """Placeholder for parser-local updates (TODO backlog item)."""
        raise NotImplementedError("MoveSteps.apply_local_update is not implemented yet.")

    def resolve_subsets(self) -> MoveSteps:
        """Placeholder for subset-aware step parsing (TODO backlog item)."""
        raise NotImplementedError("MoveSteps.resolve_subsets is not implemented yet.")
