from __future__ import annotations

from enum import Enum
from enum import StrEnum
from enum import unique


@unique
class Status(Enum):
    success = "success"
    failure = "failure"


@unique
class SearchSide(StrEnum):
    normal = "normal"
    inverse = "inverse"
    both = "both"

    def toggle(self) -> SearchSide:
        if self is SearchSide.normal:
            return SearchSide.inverse
        if self is SearchSide.inverse:
            return SearchSide.normal
        raise ValueError(f"toggle() is not defined for {self!r}")
