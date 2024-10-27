from functools import lru_cache
from functools import reduce

import numpy as np

from rubiks_cube.configuration import CUBE_SIZE
from rubiks_cube.configuration.enumeration import Piece
from rubiks_cube.configuration.type_definitions import CubeMask
from rubiks_cube.configuration.type_definitions import CubeState
from rubiks_cube.move.generator import MoveGenerator
from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.state.permutation import apply_moves_to_state
from rubiks_cube.state.permutation import get_identity_permutation


def get_ones_mask(cube_size: int = CUBE_SIZE) -> CubeMask:
    """Return the ones mask of the cube.

    Args:
        cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.

    Returns:
        CubeMask: Identity mask.
    """

    assert 1 <= cube_size <= 10, "Size must be between 1 and 10."

    return np.ones(6 * cube_size**2, dtype=bool)


def get_zeros_mask(cube_size: int = CUBE_SIZE) -> CubeMask:
    """Return the zeros mask of the cube.

    Args:
        cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.

    Returns:
        CubeMask: Identity mask.
    """

    assert 1 <= cube_size <= 10, "Size must be between 1 and 10."

    return np.zeros(6 * cube_size**2, dtype=bool)


def combine_masks(masks: tuple[CubeMask, ...]) -> CubeMask:
    """Find the total mask from multiple masks of progressively smaller sizes."""

    mask = masks[0].copy()
    if len(masks) > 1:
        mask[mask] = combine_masks(masks[1:])
    return mask


def get_rubiks_cube_mask(
    sequence: MoveSequence = MoveSequence(),
    invert: bool = False,
    cube_size: int = CUBE_SIZE,
) -> CubeMask:
    """Create a boolean mask of pieces that remain solved after sequence.

    Args:
        sequence (MoveSequence, optional): Move sequence. Defaults to MoveSequence().
        invert (bool, optional): Whether to invert the state. Defaults to False.
        cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.

    Returns:
        CubeMask: Boolean mask of pieces that remain solved after sequence.
    """
    identity_permutation = get_identity_permutation(cube_size=cube_size)
    permutation = apply_moves_to_state(identity_permutation, sequence, cube_size)

    mask: CubeMask
    if invert:
        mask = permutation != identity_permutation
    else:
        mask = permutation == identity_permutation

    return mask


# TODO: Deprecate
def generate_mask_symmetries(
    masks: list[CubeMask],
    generator: MoveGenerator = MoveGenerator("<x, y>"),
    max_size: int = 60,
    cube_size: int = CUBE_SIZE,
) -> list[list[CubeMask]]:
    """Generate list of mask symmetries of the cube using the generator.

    Args:
        masks (list[CubeMask]): List of masks.
        generator (MoveGenerator, optional): Move generator. Defaults to MoveGenerator("<x, y>").
        max_size (int, optional): Max size of the symmetry group. Defaults to 60.
        cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.

    Raises:
        ValueError: Symmetries is too large.

    Returns:
        list[list[CubeMask]]: List of mask symmetries.
    """

    solved_state = get_identity_permutation(cube_size=cube_size)
    permutations = [
        apply_moves_to_state(solved_state, sequence, cube_size=cube_size) for sequence in generator
    ]

    group_of_masks: list[list[CubeMask]] = [masks]
    size = len(group_of_masks)

    while True:
        for masks in group_of_masks:
            for p in permutations:
                new_masks = [mask[p] for mask in masks]
                if not any(
                    all(
                        np.array_equal(new_mask, current_mask)
                        for new_mask, current_mask in zip(new_masks, current_masks)
                    )
                    for current_masks in group_of_masks
                ):
                    group_of_masks.append(new_masks)
        if len(group_of_masks) == size:
            break
        size = len(group_of_masks)
        if size > max_size:
            raise ValueError(f"Symmetries is too large, {len(group_of_masks)} > {max_size}!")

    return group_of_masks


def generate_indices_symmetries(
    mask: CubeMask,
    generator: MoveGenerator = MoveGenerator("<x, y>"),
    cube_size: int = CUBE_SIZE,
) -> list[CubeState]:
    """Generate list of indices symmetries of the cube using the generator.

    Args:
        mask (CubeMask): Mask of the cube.
        generator (MoveGenerator, optional): Move generator. Defaults to MoveGenerator("<x, y>").
        cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.

    Returns:
        list[CubeState]: List of indices symmetries.
    """

    solved_state = get_identity_permutation(cube_size=cube_size)
    permutations = [
        apply_moves_to_state(solved_state, sequence, cube_size=cube_size) for sequence in generator
    ]

    list_of_states: list[CubeState] = [solved_state[mask]]
    size = len(list_of_states)

    while True:
        for perm in permutations:
            new_states = [perm[state] for state in list_of_states]
            for new_state in new_states:
                if not any(
                    np.array_equal(new_state, current_state) for current_state in list_of_states
                ):
                    list_of_states.append(new_state)
        if len(list_of_states) == size:
            break
        size = len(list_of_states)

    return list_of_states


def indices2ordered_mask(indices: CubeState, cube_size: int = CUBE_SIZE) -> CubeState:
    """Convert indices to an ordered mask.

    Args:
        indices (CubeState): Indices of the cube.
        cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.

    Returns:
        CubeState: Ordered mask.
    """
    solved_state = get_identity_permutation(cube_size=cube_size)
    ordered_mask = np.zeros_like(solved_state, dtype=int)
    ordered_mask[indices] = np.arange(1, len(indices) + 1)  # 1-indexed
    return ordered_mask


def indices2mask(indices: CubeState, cube_size: int = CUBE_SIZE) -> CubeMask:
    """Convert indices to a mask.

    Args:
        indices (CubeState): Indices of the cube.
        cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.

    Returns:
        CubeMask: Mask.
    """
    solved_state = get_identity_permutation(cube_size=cube_size)
    mask = np.zeros_like(solved_state, dtype=bool)
    mask[indices] = True
    return mask


def ordered_mask2indices(mask: CubeState, cube_size: int = CUBE_SIZE) -> CubeState:
    """Convert an ordered mask to indices.

    Args:
        mask (CubeState): Ordered mask.
        cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.

    Returns:
        CubeState: Indices.
    """
    indices = np.where(mask)[0]
    return indices[np.argsort(mask[indices])]


def get_example_piece_mask(piece: Piece, cube_size: int = CUBE_SIZE) -> CubeMask:
    """Return an example piece of the cube, a mask with only one index.

    Args:
        piece (Piece): Piece type.
        cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.

    Returns:
        CubeState: First example piece.
    """
    mask = np.zeros(6 * cube_size**2, dtype=bool)

    # up-front-right corner
    if piece is Piece.corner:
        mask[cube_size**2 - 1] = True
        mask[cube_size**2 + cube_size - 1] = True
        mask[2 * cube_size**2] = True

    # up-front edge (closest to the corner)
    elif piece is Piece.edge:
        mask[cube_size**2 - 2] = True
        mask[cube_size**2 + cube_size - 2] = True

    # up center
    elif piece is Piece.center:
        mask[int((cube_size**2 - 1) // 2)] = True

    return mask


@lru_cache(maxsize=1)
def get_all_piece_idx_sets(cube_size: int = CUBE_SIZE) -> list[list[int]]:
    """Return all indexes of the pieces on the cube.

    Args:
        cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.

    Returns:
        list[list[int]]: List of indexes of the pieces on the cube.
    """
    pieces = [Piece.corner, Piece.edge]
    idx_list = []
    for piece in pieces:
        mask = get_example_piece_mask(piece, cube_size=cube_size)
        idx_list.extend(
            [
                list(np.where(symmetry[0])[0])
                for symmetry in generate_mask_symmetries([mask], cube_size=cube_size)
            ]
        )
    return idx_list


def get_piece_mask(piece: Piece | list[Piece | None], cube_size: int = CUBE_SIZE) -> CubeMask:
    """Return a mask for the piece type.

    Args:
        pieces (Piece | list[Piece]): Piece type(s).
        cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.

    Returns:
        CubeMask: Mask for the piece type.
    """

    if isinstance(piece, list):
        mask = get_zeros_mask(cube_size=cube_size)
        for p in piece:
            if p is not None:
                mask |= get_piece_mask(p, cube_size=cube_size)
        return mask

    face_mask = np.zeros((cube_size, cube_size), dtype=bool)
    if piece is Piece.corner:
        if cube_size == 1:
            face_mask[0, 0] = True
        elif cube_size > 1:
            face_mask[0, 0] = True
            face_mask[0, cube_size - 1] = True
            face_mask[cube_size - 1, 0] = True
            face_mask[cube_size - 1, cube_size - 1] = True
    elif piece is Piece.edge:
        if cube_size > 2:
            face_mask[0, 1 : cube_size - 1] = True
            face_mask[cube_size - 1, 1 : cube_size - 1] = True
            face_mask[1 : cube_size - 1, 0] = True
            face_mask[1 : cube_size - 1, cube_size - 1] = True
    elif piece is Piece.center:
        if cube_size > 2:
            face_mask[1 : cube_size - 1, 1 : cube_size - 1] = True

    return np.tile(face_mask.flatten(), 6)


def unorientate_mask(mask: CubeMask, cube_size: int = CUBE_SIZE) -> CubeMask:
    """Turn the orientated mask into an unorientated mask.

    Args:
        mask (CubeMask): Mask of the cube.
        cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.

    Returns:
        CubeMask: Unorientated mask.
    """
    new_mask = mask.copy()
    for idx in np.where(mask)[0]:
        for piece_idx_list in get_all_piece_idx_sets(cube_size=cube_size):
            if idx in piece_idx_list:
                new_mask[piece_idx_list] = True
    return new_mask


def get_generator_orientation(
    piece: Piece,
    generator: MoveGenerator,
    cube_size: int = CUBE_SIZE,
) -> list[CubeMask]:
    """Return a list of masks for the piece orientation.

    Args:
        piece (Piece): Piece type.
        generator (MoveGenerator): Move generator.
        cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.

    Returns:
        list[CubeMask]: List of masks for the piece orientation.
    """

    # All indexes of the piece on the cube
    piece_mask = get_piece_mask(piece, cube_size)

    # All indexes of the piece affected by the generator
    affected_mask = reduce(
        np.logical_or,
        (
            get_rubiks_cube_mask(sequence=sequence, invert=True, cube_size=cube_size)
            for sequence in generator
        ),
    )

    # All indexes of the piece affected by the generator
    affected_piece_mask = piece_mask & affected_mask

    # Keep track of all orientations
    orientations = []

    # Loop over all orientations of the piece
    while np.any(affected_piece_mask):

        # Index of the first oriented piece
        oriented_piece = np.argmax(affected_piece_mask)

        # Mask for the oriented piece
        solved_state = get_identity_permutation(cube_size=cube_size)
        mask = np.zeros_like(solved_state, dtype=bool)
        mask[oriented_piece] = True

        # All symmetries for the piece
        symmetries = generate_mask_symmetries(
            masks=[mask],
            generator=generator,
            cube_size=cube_size,
        )
        # unpack the first element in the lists
        symmetry_group = [symmetry[0] for symmetry in symmetries]

        # All symmetries for the piece
        orientated_mask = reduce(np.logical_or, symmetry_group)
        unorientated_mask = unorientate_mask(orientated_mask, cube_size=cube_size)

        orientations.append(orientated_mask)

        # Remove the un-oriented mask
        affected_piece_mask[unorientated_mask] = False

    return orientations


def generate_permutation_symmetries(
    mask: CubeMask,
    generator: MoveGenerator = MoveGenerator("<x, y>"),
    max_size: int = 60,
    cube_size: int = CUBE_SIZE,
) -> list[CubeState]:
    """Generate list of permutations of the cube using the generator.

    Args:
        mask (CubeMask): Mask of the cube.
        generator (MoveGenerator, optional): Move generator. Defaults to MoveGenerator("<x, y>").
        max_size (int, optional): Max size of the symmetries. Defaults to 60.
        cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.

    Raises:
        ValueError: Symmetries is too large.

    Returns:
        list[CubeState]: List of permutations.
    """

    solved_state = get_identity_permutation(cube_size=cube_size)
    permutations = [
        apply_moves_to_state(solved_state, sequence, cube_size=cube_size) for sequence in generator
    ]

    list_of_permutations: list[CubeState] = [solved_state]
    size = len(list_of_permutations)

    while True:
        for current_permutation in list_of_permutations:
            for permutation in permutations:
                new_permutation = current_permutation[permutation]
                if not any(
                    np.array_equal(mask[new_permutation], mask[perm])
                    for perm in list_of_permutations
                ):
                    list_of_permutations.append(new_permutation)
        if len(list_of_permutations) == size:
            break
        size = len(list_of_permutations)
        if size > max_size:
            raise ValueError(f"Symmetries is too large, {len(list_of_permutations)} > {max_size}!")

    return list_of_permutations


def orientations_are_equal(orients1: list[CubeState], orients2: list[CubeState]) -> bool:
    """Check if two orientations are equal.

    Args:
        orients1 (list[CubeState]): First list of orientations.
        orients2 (list[CubeState]): Second list of orientations.

    Returns:
        bool: Whether the orientations are equal.
    """

    while orients1:
        orient1 = orients1.pop()
        for i, orient2 in enumerate(orients2):
            if np.array_equal(orient1, orient2):
                del orients2[i]
                break
        else:
            return False
    return not orients2
