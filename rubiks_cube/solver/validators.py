"""Registry of named permutation validators for serialization round-trips."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rubiks_cube.autotagger.subset import distinguish_htr

if TYPE_CHECKING:
    from rubiks_cube.configuration.types import PermutationValidator

VALIDATOR_REGISTRY: dict[str, PermutationValidator] = {
    "htr": lambda permutation: distinguish_htr(permutation) == "real",
}
