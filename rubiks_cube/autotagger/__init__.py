from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from typing import Final

import numpy as np

from rubiks_cube.autotagger.cubex import get_cubexes
from rubiks_cube.autotagger.step import TAG_TO_TAG_STEPS
from rubiks_cube.autotagger.subset import get_subset_label
from rubiks_cube.configuration import CUBE_SIZE
from rubiks_cube.configuration.enumeration import Goal
from rubiks_cube.representation.pattern import get_empty_pattern

if TYPE_CHECKING:
    from rubiks_cube.configuration.types import CubePattern
    from rubiks_cube.configuration.types import CubePermutation

LOGGER: Final = logging.getLogger(__name__)
DR_TAGS: Final[set[str]] = {Goal.dr_ud.value, Goal.dr_fb.value, Goal.dr_lr.value}


def _to_step_tag(tag: str, subset: str | None) -> str:
    """Normalize tags used in step labeling."""
    if tag == Goal.htr_like.value:
        if subset == "real":
            return Goal.htr.value
        if subset == "fake":
            return Goal.fake_htr.value
    return tag


def get_rubiks_cube_patterns(goal: Goal, cube_size: int = CUBE_SIZE) -> list[CubePattern]:
    """Get matchable Rubik's cube patterns from the goal.

    Args:
        goal (Goal): Goal to solve.
        subset (str | None, optional): Subset of the goal. Defaults to None.
        cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.
    """
    if goal is Goal.none:
        return [get_empty_pattern(cube_size=cube_size)]

    # Real HTR matches on HTR lookalike, then filters out the real subset
    if goal is Goal.htr:
        goal = Goal.htr_like

    cubexes = get_cubexes(cube_size=cube_size)
    if goal not in cubexes:
        raise ValueError("Cannot create the pattern for the given goal and cube size.")

    return cubexes[goal].patterns


def autotag_permutation_with_subset(
    permutation: CubePermutation,
    cube_size: int = CUBE_SIZE,
) -> tuple[str, str | None]:
    """Autotag the permutation and optionally return a subset label.

    Args:
        permutation (CubePermutation): Cube permutation.
        cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.

    Returns:
        tuple[str, str | None]: Tag and optional subset label.
    """
    # Match with first cubex in entropy-increasing order
    for goal, cubex in get_cubexes(cube_size=cube_size).items():
        if cubex.match(permutation):
            tag = goal.value
            break
    else:
        tag = Goal.none.value

    subset = get_subset_label(tag, permutation)
    return tag, subset


def autotag_permutation(permutation: CubePermutation, cube_size: int = CUBE_SIZE) -> str:
    """Autotag the permutation.

    Args:
        permutation (CubePermutation): Cube permutation.
        cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.

    Returns:
        str: Tag for the permutation.
    """
    tag, _subset = autotag_permutation_with_subset(permutation, cube_size=cube_size)
    return tag


def autotag_step(
    initial_permutation: CubePermutation,
    final_permutation: CubePermutation,
    cube_size: int = CUBE_SIZE,
) -> str:
    """Autotag the step.

    Args:
        initial_permutation (CubePermutation): Initial permutation.
        final_permutation (CubePermutation): Final permutation.
        cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.

    Returns:
        str: Tag of the step.
    """
    if np.array_equal(initial_permutation, final_permutation):
        return "nothing"

    initial_tag_raw, initial_subset = autotag_permutation_with_subset(
        initial_permutation,
        cube_size=cube_size,
    )
    final_tag_raw, final_subset = autotag_permutation_with_subset(
        final_permutation,
        cube_size=cube_size,
    )
    initial_tag = _to_step_tag(initial_tag_raw, initial_subset)
    final_tag = _to_step_tag(final_tag_raw, final_subset)

    if step := TAG_TO_TAG_STEPS.get((initial_tag, final_tag)):
        if step in DR_TAGS and final_subset is not None:
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
