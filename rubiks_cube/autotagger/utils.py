from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Self  # ty: ignore[unresolved-import]

import attrs
import numpy as np

from rubiks_cube.autotagger.interface import PermutationTagger
from rubiks_cube.autotagger.pattern import get_patterns
from rubiks_cube.autotagger.step import DR_STEPS
from rubiks_cube.autotagger.step import TAG_TO_TAG_STEPS
from rubiks_cube.autotagger.subset import get_subset_label
from rubiks_cube.configuration.enumeration import Goal

if TYPE_CHECKING:
    from rubiks_cube.autotagger.pattern import Pattern
    from rubiks_cube.configuration.types import CubePermutation


def _to_step_tag(tag: str, subset: str | None) -> str:
    """Normalize tags used in step labeling."""
    if tag == Goal.htr_like.value:
        if subset == "real":
            return Goal.htr.value
        if subset == "fake":
            return Goal.fake_htr.value
    return tag


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
        subset = get_subset_label(tag, permutation)
        return tag, subset

    def tag_step(
        self,
        initial_permutation: CubePermutation,
        final_permutation: CubePermutation,
    ) -> str:
        """Autotag the step from the initial to the final permutation."""
        if np.array_equal(initial_permutation, final_permutation):
            return "nothing"

        initial_tag_raw, initial_subset = self.tag_with_subset(initial_permutation)
        final_tag_raw, final_subset = self.tag_with_subset(final_permutation)
        initial_tag = _to_step_tag(initial_tag_raw, initial_subset)
        final_tag = _to_step_tag(final_tag_raw, final_subset)

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
