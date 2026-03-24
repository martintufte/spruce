from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from typing import TYPE_CHECKING
from typing import Generic
from typing import TypeVar

if TYPE_CHECKING:
    from collections.abc import Sequence

    from rubiks_cube.configuration.types import PermutationArray

Ttag = TypeVar("Ttag")


class PermutationTagger(ABC, Generic[Ttag]):
    tags: Sequence[Ttag]

    @abstractmethod
    def tag(self, permutation: PermutationArray) -> Ttag: ...

    @abstractmethod
    def tag_step(
        self, initial_permutation: PermutationArray, final_permutation: PermutationArray
    ) -> str: ...
