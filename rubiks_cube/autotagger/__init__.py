from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Self  # ty: ignore[unresolved-import]

import attrs
import numpy as np

from rubiks_cube.autotagger.interface import PermutationTagger
from rubiks_cube.autotagger.pattern import get_patterns
from rubiks_cube.autotagger.step import DR_STEPS
from rubiks_cube.autotagger.step import TAG_TO_TAG_STEPS
from rubiks_cube.autotagger.subset import get_dr_subset_label
from rubiks_cube.configuration import CUBE_SIZE
from rubiks_cube.configuration.enumeration import Goal

if TYPE_CHECKING:
    from rubiks_cube.autotagger.pattern import Pattern
    from rubiks_cube.configuration.types import CubePermutation


@attrs.frozen
class PatternTagger(PermutationTagger):
    patterns: dict[Goal, Pattern]

    @property
    def tags(self) -> list[str]:
        return [goal.value for goal in self.patterns]

    @classmethod
    def from_cube_size(cls, cube_size: int) -> Self:
        return cls(patterns=get_patterns(cube_size=cube_size))

    def tag(self, permutation: CubePermutation) -> str:
        """Tag by matching patterns in entropy-increasing order."""
        for goal, pattern in self.patterns.items():
            if pattern.match(permutation):
                tag = goal.value
                break
        else:
            tag = Goal.none.value

        return tag

    def tag_with_subset(self, permutation: CubePermutation) -> tuple[str, str | None]:
        tag = self.tag(permutation=permutation)
        subset: str | None = None
        if tag == "htr-like":
            tag = "fake htr"
        elif tag in ["dr-ud", "dr-fb", "dr-lr"]:
            subset = get_dr_subset_label(tag, permutation)

        return tag, subset

    def tag_step(
        self,
        initial_permutation: CubePermutation,
        final_permutation: CubePermutation,
    ) -> str:
        """Autotag the step from the initial to the final permutation."""
        if np.array_equal(initial_permutation, final_permutation):
            return "nothing"

        initial_tag, _initial_subset = self.tag_with_subset(initial_permutation)
        final_tag, final_subset = self.tag_with_subset(final_permutation)

        if step := TAG_TO_TAG_STEPS.get((initial_tag, final_tag)):
            if step in DR_STEPS and final_subset is not None:
                return f"{step} [{final_subset}]"
            return step
        step = f"{initial_tag} -> {final_tag}"
        if initial_tag == Goal.none.value != final_tag:
            return final_tag
        if initial_tag != Goal.solved.value == final_tag:
            return "finish"
        if initial_tag == final_tag:
            return "random moves"
        return step


def autotag_permutation(
    permutation: CubePermutation,
    include_subset: bool = False,
    cube_size: int = CUBE_SIZE,
) -> str:
    """Autotag the permutation.

    Args:
        permutation (CubePermutation): Cube permutation.
        include_subset (bool, optional): Whether to include the subset in the tag.
            Defaults to False.
        cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.

    Returns:
        str: Tag for the permutation. If subset is found, included as [].
    """
    autotagger = PatternTagger.from_cube_size(cube_size=cube_size)

    if include_subset:
        tag, subset = autotagger.tag_with_subset(permutation=permutation)
    else:
        tag = autotagger.tag(permutation=permutation)
        subset = None

    return f"{tag} [{subset}]" if subset is not None else tag


def autotag_step(
    initial_permutation: CubePermutation,
    final_permutation: CubePermutation,
    cube_size: int = CUBE_SIZE,
) -> str:
    """Autotag the step between the initial and the final permutation.

    Args:
        initial_permutation (CubePermutation): Initial cube permutation.
        final_permutation (CubePermutation): Final cube permutation.
        cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.

    Returns:
        str: Tag for the permutation.
    """
    # Setup the AutoTagger to use
    autotagger = PatternTagger.from_cube_size(cube_size=cube_size)

    tag = autotagger.tag_step(
        initial_permutation=initial_permutation,
        final_permutation=final_permutation,
    )

    return tag
