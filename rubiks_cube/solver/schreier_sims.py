"""BFS-based group membership testing for permutation groups.

This module implements a breadth-first search approach to:
1. Generate the elements of a permutation group up to a size limit
2. Test if a given permutation belongs to the group

Note: For large groups (like full Rubik's cube with 10^19 states), this approach
is limited by memory. It's practical for small subgroups like <R, U> or specific
move restrictions that generate tractable group sizes.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from typing import Final

import numpy as np

from rubiks_cube.configuration import CUBE_SIZE
from rubiks_cube.representation import get_rubiks_cube_state
from rubiks_cube.representation.permutation import get_identity_permutation

if TYPE_CHECKING:
    from rubiks_cube.configuration.types import CubePermutation
    from rubiks_cube.move.generator import MoveGenerator

LOGGER: Final = logging.getLogger(__name__)

# Maximum group size to prevent memory exhaustion
MAX_GROUP_SIZE = 1000000


def _perm_to_tuple(perm: CubePermutation) -> tuple[int, ...]:
    """Convert permutation array to hashable tuple.

    Args:
        perm (CubePermutation): Permutation array.

    Returns:
        tuple[int, ...]: Tuple representation.
    """
    return tuple(perm.tolist())


def _generate_group(
    generators: list[CubePermutation],
    max_size: int = MAX_GROUP_SIZE,
) -> set[tuple[int, ...]]:
    """Generate all elements of the group up to max_size using BFS.

    Args:
        generators (list[CubePermutation]): Generator permutations.
        max_size (int, optional): Maximum group size. Defaults to MAX_GROUP_SIZE.

    Returns:
        set[tuple[int, ...]]: Set of all group elements as tuples.
    """
    if not generators:
        return set()

    # Start with identity
    identity = generators[0].copy()
    identity[:] = np.arange(len(identity))

    group: set[tuple[int, ...]] = {_perm_to_tuple(identity)}
    queue: list[CubePermutation] = [identity.copy()]
    queue_idx = 0

    while queue_idx < len(queue) and len(group) < max_size:
        current = queue[queue_idx]
        queue_idx += 1

        # Apply each generator to current element
        for gen in generators:
            # Compose: current followed by gen
            new_perm = current[gen]
            new_tuple = _perm_to_tuple(new_perm)

            if new_tuple not in group:
                group.add(new_tuple)
                queue.append(new_perm.copy())

            # Also try inverse direction: gen followed by current
            inv_perm = gen[current]
            inv_tuple = _perm_to_tuple(inv_perm)

            if inv_tuple not in group:
                group.add(inv_tuple)
                queue.append(inv_perm.copy())

    if len(group) >= max_size:
        LOGGER.warning(
            f"Group generation reached maximum size {max_size}. "
            "Group may be larger. Membership test may give false negatives."
        )

    return group


def is_solvable(
    permutation: CubePermutation,
    generator: MoveGenerator,
    cube_size: int = CUBE_SIZE,
    max_group_size: int = MAX_GROUP_SIZE,
) -> bool:
    """Check if a permutation is solvable using the given generator.

    Generates all elements of the group and checks if the permutation is in it.

    Args:
        permutation (CubePermutation): The permutation to test.
        generator (MoveGenerator): Set of allowed moves (generators).
        cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.
        max_group_size (int, optional): Max group size to generate. Defaults to MAX_GROUP_SIZE.

    Returns:
        bool: True if the permutation is solvable with the generator.

    Example:
        >>> from rubiks_cube.move.generator import MoveGenerator
        >>> from rubiks_cube.representation import get_rubiks_cube_state
        >>> from rubiks_cube.move.sequence import MoveSequence
        >>>
        >>> gen = MoveGenerator("<R, U>")
        >>> scramble = MoveSequence("R U R' U'")
        >>> perm = get_rubiks_cube_state(scramble)
        >>> is_solvable(perm, gen)
        True
    """
    identity = get_identity_permutation(cube_size=cube_size)

    # If permutation is identity, it's trivially solvable
    if np.array_equal(permutation, identity):
        return True

    # Convert generator moves to permutations
    generator_perms: list[CubePermutation] = []
    for move_seq in generator.generator:
        perm = get_rubiks_cube_state(move_seq, cube_size=cube_size)
        generator_perms.append(perm)

    # Handle empty generator
    if not generator_perms:
        return np.array_equal(permutation, identity)

    # Generate the group
    group = _generate_group(generator_perms, max_size=max_group_size)

    # Check if permutation is in the group
    perm_tuple = _perm_to_tuple(permutation)
    return perm_tuple in group


def get_group_order(
    generator: MoveGenerator,
    cube_size: int = CUBE_SIZE,
    max_group_size: int = MAX_GROUP_SIZE,
) -> int:
    """Compute the order (size) of the group generated by the given moves.

    Warning:
        This can be extremely large for full cube generators (>10^19).
        Use with caution on small generators only.

    Args:
        generator (MoveGenerator): Set of generator moves.
        cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.
        max_group_size (int, optional): Max group size to generate. Defaults to MAX_GROUP_SIZE.

    Returns:
        int: The order of the group (or max_group_size if group is larger).
    """
    # Convert generator moves to permutations
    generator_perms: list[CubePermutation] = []
    for move_seq in generator.generator:
        perm = get_rubiks_cube_state(move_seq, cube_size=cube_size)
        generator_perms.append(perm)

    if not generator_perms:
        return 1

    # Generate the group
    group = _generate_group(generator_perms, max_size=max_group_size)

    return len(group)
