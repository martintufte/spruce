from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from typing import TYPE_CHECKING
from typing import Generic
from typing import TypeVar

if TYPE_CHECKING:
    from collections.abc import Sequence

    from rubiks_cube.configuration.types import CubePermutation

Ttag = TypeVar("Ttag")


class PermutationTagger(ABC, Generic[Ttag]):
    tags: Sequence[Ttag]

    @abstractmethod
    def tag(self, permutation: CubePermutation) -> Ttag: ...
