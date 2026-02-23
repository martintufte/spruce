from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from rubiks_cube.autotagger.cubex import get_cubexes
from rubiks_cube.autotagger.utils import CubexTagger
from rubiks_cube.configuration import CUBE_SIZE
from rubiks_cube.configuration.enumeration import Goal
from rubiks_cube.representation.pattern import get_empty_pattern

if TYPE_CHECKING:
    from rubiks_cube.configuration.types import CubePattern
    from rubiks_cube.configuration.types import CubePermutation

LOGGER = logging.getLogger(__name__)


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
    autotagger = CubexTagger.from_cube_size(cube_size=cube_size)

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
    autotagger = CubexTagger.from_cube_size(cube_size=cube_size)

    tag = autotagger.tag_step(
        initial_permutation=initial_permutation,
        final_permutation=final_permutation,
    )

    return tag
