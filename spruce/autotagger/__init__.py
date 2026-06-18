from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Self

import attrs
import numpy as np

from spruce.autotagger.interface import PermutationTagger
from spruce.autotagger.pattern import get_patterns
from spruce.autotagger.step import TAG_TO_TAG_STEPS
from spruce.autotagger.subset import get_dr_subset_label
from spruce.configuration.enumeration import Goal
from spruce.configuration.enumeration import Variant

if TYPE_CHECKING:
    from spruce.autotagger.pattern import Pattern
    from spruce.move.meta import MoveMeta
    from spruce.types import PermutationArray


@attrs.frozen
class PatternTagger(PermutationTagger):
    patterns: dict[Goal, Pattern]
    move_meta: MoveMeta

    @property
    def tags(self) -> list[str]:
        return [goal.value for goal in self.patterns]

    @classmethod
    def from_move_meta(cls, move_meta: MoveMeta) -> Self:
        return cls(patterns=get_patterns(puzzle=move_meta.puzzle), move_meta=move_meta)

    def tag(self, permutation: PermutationArray) -> str:
        """Tag by matching patterns in entropy-increasing order."""
        for goal, pattern in self.patterns.items():
            if variant := pattern.match(permutation):
                tag = f"{goal.value}"
                if variant is not Variant.none:
                    tag += f".{variant.value}"
                break
        else:
            tag = Goal.none.value

        return tag

    def tag_with_subset(self, permutation: PermutationArray) -> tuple[str, str | None]:
        tag = self.tag(permutation=permutation)
        subset: str | None = None
        if tag == Goal.htr_like.value:
            tag = Goal.fake_htr.value
        elif tag in ["dr.ud", "dr.fb", "dr.lr"]:
            subset = get_dr_subset_label(tag, permutation, move_meta=self.move_meta)

        return tag, subset

    def tag_step(
        self,
        initial_permutation: PermutationArray,
        final_permutation: PermutationArray,
    ) -> str:
        """Autotag the step from the initial to the final permutation."""
        if np.array_equal(initial_permutation, final_permutation):
            return "nothing"

        initial_tag, _initial_subset = self.tag_with_subset(initial_permutation)
        final_tag, final_subset = self.tag_with_subset(final_permutation)

        step = TAG_TO_TAG_STEPS.get((initial_tag, final_tag), f"{initial_tag} -> {final_tag}")

        if initial_tag == Goal.none.value != final_tag:
            step = final_tag
        elif initial_tag != Goal.solved.value == final_tag:
            step = "finish"
        elif initial_tag == final_tag:
            step = "random moves"

        if final_subset is not None:
            return f"{step} [{final_subset}]"
        return step


def autotag_permutation(
    permutation: PermutationArray,
    move_meta: MoveMeta,
    include_subset: bool = False,
) -> str:
    """Autotag the permutation.

    Args:
        permutation (PermutationArray): Permutation.
        move_meta (MoveMeta): Meta information about moves.
        include_subset (bool, optional): Whether to include the subset in the tag.
            Defaults to False.

    Returns:
        str: Tag for the permutation. If subset is found, included as [].
    """
    autotagger = PatternTagger.from_move_meta(move_meta=move_meta)

    if include_subset:
        tag, subset = autotagger.tag_with_subset(permutation=permutation)
    else:
        tag = autotagger.tag(permutation=permutation)
        subset = None

    return f"{tag} [{subset}]" if subset is not None else tag
