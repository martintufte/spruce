from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from rubiks_cube.autotagger.utils import PatternTagger
from rubiks_cube.configuration import CUBE_SIZE

if TYPE_CHECKING:
    from rubiks_cube.configuration.types import CubePermutation

LOGGER = logging.getLogger(__name__)


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
        if tag == "htr-like":
            if subset == "fake":
                tag = "fake htr"
                subset = None
            else:
                tag = "htr"
                subset = None
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
