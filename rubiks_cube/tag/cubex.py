from __future__ import annotations

from functools import lru_cache
from functools import reduce
from typing import Any
from typing import Literal

import numpy as np

from rubiks_cube.configuration import CUBE_SIZE
from rubiks_cube.configuration.enumeration import Piece
from rubiks_cube.configuration.enumeration import Progress
from rubiks_cube.configuration.enumeration import State
from rubiks_cube.configuration.type_definitions import CubeState
from rubiks_cube.move.generator import MoveGenerator
from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.state import get_rubiks_cube_state
from rubiks_cube.state.mask import create_mask_from_sequence
from rubiks_cube.state.mask import generate_indices_symmetries
from rubiks_cube.state.mask import generate_mask_symmetries
from rubiks_cube.state.mask import generate_permutation_symmetries
from rubiks_cube.state.mask import get_generator_orientation
from rubiks_cube.state.mask import indices2mask
from rubiks_cube.state.mask import indices2ordered_mask
from rubiks_cube.state.mask import ordered_mask2indices
from rubiks_cube.state.permutation import get_identity_permutation


class Cubex:
    """Cube Expression, a pattern that can be matched against a cube state.

    It consists of the following:
    - mask: A boolean mask that represents the fixed pieces to check.
    - relative_masks: A list of boolean masks that must be relative.
    - orientations: A list of boolean masks that represent the relative pieces.
    """

    def __init__(
        self,
        mask: CubeState | None = None,
        relative_masks: list[list[CubeState]] | None = None,
        orientations: list[CubeState] | None = None,
        cube_size: int = CUBE_SIZE,
    ) -> None:
        """Initialize the cube pattern.

        Args:
            mask (CubeState | None, optional): Mask of pieces that must be solved. Defaults to None.
            relative_masks (list[list[CubeState]] | None, optional):
                List of list of relativly solved pieces. Defaults to None.
            orientations (list[CubeState] | None, optional): List of orientations. Defaults to None.
            cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.
        """
        self.mask = mask if mask is not None else np.zeros(6 * cube_size**2, dtype=bool)
        self.relative_masks = relative_masks or []
        self.orientations = orientations or []
        self.size = cube_size
        assert len(self.mask) == 6 * cube_size**2, "Invalid mask size!"

    def __repr__(self) -> str:
        if np.sum(self.mask) == 0:
            mask_repr = "None"
        else:
            mask_repr = str(self.mask)
        return f"Cubex(mask={mask_repr}, \
            orientations={self.orientations}), \
            relative_masks={self.relative_masks}"

    def _match_mask(self, permutation: CubeState, goal: CubeState) -> bool:
        return np.array_equal(permutation[self.mask], goal[self.mask])

    def _match_relative_masks(self, permutation: CubeState, goal: CubeState) -> bool:
        if len(self.relative_masks) == 0:
            return True
        return all(
            self._match_relative_mask(relative_mask, permutation, goal)
            for relative_mask in self.relative_masks
        )

    def _match_relative_mask(
        self, relative_mask: list[CubeState], permutation: CubeState, goal: CubeState
    ) -> bool:

        perm_set = permutation[relative_mask[0]]
        goal_sets = [goal[relative_mask_in] for relative_mask_in in relative_mask]
        return any(np.array_equal(perm_set, goal_set) for goal_set in goal_sets)

    def _match_orientations(self, permutation: CubeState, goal: CubeState) -> bool:
        return all(
            np.all(np.isin(permutation[orientation], goal[orientation]))
            for orientation in self.orientations
        )

    def match(
        self,
        state: CubeState,
        goal: CubeState,
    ) -> bool:
        """Check if the state matches the pattern.

        Args:
            state (CubeState): Cube state to check.
            goal (CubeState): Goal state.

        Returns:
            bool: Whether the state matches the pattern.
        """
        return (
            self._match_mask(state, goal)
            and self._match_relative_masks(state, goal)
            and self._match_orientations(state, goal)
        )

    def __and__(self, other: Cubex) -> Cubex:
        """
        Combine two cube expressions with the AND operation.
        This will match the union of the two patterns.
        """
        return Cubex(
            mask=self.mask | other.mask,
            orientations=self.orientations + other.orientations,
            relative_masks=self.relative_masks + other.relative_masks,
            cube_size=self.size,
        )

    def __rand__(self, other: Cubex) -> Cubex:
        return self & other

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Cubex):
            return hash(self) == hash(other)
        return False

    def __hash__(self) -> int:
        return hash(
            (
                self.mask.tobytes(),
                tuple(orientation.tobytes() for orientation in self.orientations),
                tuple(relative_mask[0].tobytes() for relative_mask in self.relative_masks),
            )
        )

    def permute(self, state: CubeState, cube_size: int = CUBE_SIZE) -> Cubex:
        """Permute the pattern with the permutation.

        Args:
            state (CubeState): State to permute with.
            cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.

        Returns:
            Cubex: Permuted pattern.
        """
        if not self.relative_masks:
            return Cubex(
                mask=self.mask[state],
                orientations=[orientation[state] for orientation in self.orientations],
                relative_masks=[],
                cube_size=cube_size,
            )
        return Cubex(
            mask=self.mask[state],
            orientations=[orientation[state] for orientation in self.orientations],
            relative_masks=[
                [
                    ordered_mask2indices(indices2ordered_mask(indecies, cube_size=cube_size)[state])
                    for indecies in relative_mask
                ]
                for relative_mask in self.relative_masks
            ],
            cube_size=cube_size,
        )

    def create_symmetries(self) -> list[Cubex]:
        """Create all symmetries that matches the pattern.

        Returns:
            list[Cubex]: List of symmetries from the pattern.
        """

        # create all symmetries from the masks
        mask = reduce(np.logical_or, [self.mask] + self.orientations)
        states = generate_permutation_symmetries(mask, cube_size=self.size)

        # Create CubePatterns from the states
        return [self.permute(state=state, cube_size=self.size) for state in states]


class CubexCollection:
    """Cube Expression Collection."""

    def __init__(
        self,
        patterns: list[Cubex],
        keep: bool = True,
    ) -> None:
        """Initialize the cube expression.

        Args:
            patterns (list[Cubex]): List of cube patterns.
            keep (bool, optional): Whether to keep the pattern. Defaults to True.
        """
        self.patterns = list(set(patterns))
        self.keep = keep

    def __repr__(self) -> str:
        return f"CubexCollection(patterns={self.patterns})"

    def __or__(self, other: CubexCollection) -> CubexCollection:
        return CubexCollection(
            patterns=[*self.patterns, *other.patterns], keep=self.keep or other.keep
        )

    def __ror__(self, other: CubexCollection) -> CubexCollection:
        return self | other

    def __and__(self, other: CubexCollection) -> CubexCollection:
        return CubexCollection(
            patterns=[
                pattern & other_pattern
                for pattern in self.patterns
                for other_pattern in other.patterns
            ],
            keep=self.keep or other.keep,
        )

    def __rand__(self, other: CubexCollection) -> CubexCollection:
        return self & other

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, CubexCollection):
            return self.patterns == other.patterns
        return False

    def __len__(self) -> int:
        return len(self.patterns)

    def match(self, input: MoveSequence | CubeState, cube_size: int = CUBE_SIZE) -> bool:
        """Check if the permutation matches any of the patterns.

        Args:
            input (MoveSequence | CubeState): Input to check.
            cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.

        Returns:
            bool: Whether the input matches any of the patterns.
        """
        if isinstance(input, MoveSequence):
            permutation = get_rubiks_cube_state(
                sequence=input,
                orientate_after=True,
                cube_size=cube_size,
            )
        else:
            permutation = input
        goal = get_identity_permutation(cube_size=cube_size)
        return any(pattern.match(permutation, goal=goal) for pattern in self.patterns)

    @classmethod
    def from_solved_after_sequence(
        cls,
        sequence: MoveSequence = MoveSequence(),
        invert: bool = False,
        kind: Literal["permutation", "orientation"] = "permutation",
        keep: bool = True,
        cube_size: int = CUBE_SIZE,
    ) -> CubexCollection:
        """Create a cube expression from the pieces that are solved after
        applying a sequence of moves.

        Args:
            sequence (MoveSequence, optional): Move sequence. Defaults to MoveSequence().
            invert (bool, optional): Wether to invert afterwards. Defaults to False.
            kind (Literal["permutation", "orientation"], optional): Kind. Defaults to "permutation".
            keep (bool, optional): Wether to keep the pattern. Defaults to True.
            cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.

        Returns:
            CubexCollection: Cube expression.
        """
        mask = create_mask_from_sequence(sequence=sequence, invert=invert, cube_size=cube_size)
        if kind == "orientation":
            return cls([Cubex(orientations=[mask], cube_size=cube_size)], keep=keep)
        elif kind == "permutation":
            return cls([Cubex(mask=mask, cube_size=cube_size)], keep=keep)

    @classmethod
    def from_generator_orientation(
        cls,
        pieces: list[Piece],
        generator: MoveGenerator,
        keep: bool = True,
        cube_size: int = CUBE_SIZE,
    ) -> CubexCollection:
        """Create a cube expression from a the orientation that is perserved
        in the generator. Generator is a sequence of moves that "generates" the
        orientation.

        Args:
            pieces (list[Piece]): List of pieces.
            generator (MoveGenerator): Move generator.
            keep (bool, optional): Wether to keep the pattern. Defaults to True.
            cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.

        Returns:
            CubexCollection: Cube expression.
        """
        orientations = []

        for piece in pieces:
            orientations.extend(
                get_generator_orientation(
                    piece=piece,
                    generator=generator,
                    cube_size=cube_size,
                )
            )

        if orientations:
            return cls([Cubex(orientations=orientations, cube_size=cube_size)], keep=keep)
        return cls([], keep=keep)

    @classmethod
    def from_relativly_solved(
        cls,
        sequence: MoveSequence,
        generator: MoveGenerator,
        keep: bool = True,
        cube_size: int = CUBE_SIZE,
    ) -> CubexCollection:
        """Create a cube expression from a sequence. The pieces affected by the
        sequence are considered solved. Then it will automatically find the
        pieces that are affected in the same way, i.e. the location relative to
        the other piece is the same.

        Args:
            sequence (MoveSequence): Move sequence.
            generator (MoveGenerator): Move generator.
            keep (bool, optional): Wether to keep the pattern. Defaults to True.
            cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.

        Returns:
            CubexCollection: Cube expression.
        """
        mask = create_mask_from_sequence(sequence=sequence, cube_size=cube_size)
        group_of_masks = generate_mask_symmetries(
            masks=[mask],
            generator=generator,
            cube_size=cube_size,
        )
        # unpack the group of relative masks
        masks = [group[0] for group in group_of_masks]

        # generate the relative masks
        relative_masks = [
            generate_indices_symmetries(
                mask=mask,
                generator=generator,
                cube_size=cube_size,
            )
            for mask in masks
        ]

        return cls([Cubex(relative_masks=relative_masks, cube_size=cube_size)], keep=keep)

    def create_symmetries(self) -> None:
        """Create symmetries for the cube expression only if it has a mask."""
        new_patterns = []
        for pattern in self.patterns:
            new_patterns.extend(pattern.create_symmetries())
        self.patterns = new_patterns

    def optimize(self) -> None:
        """Optimize the cube expression.

        Unit tests:
            TODO: Remove idx from a orientation if it is in the mask.
            -> FIXED

            TODO: Remove duplicate orientations that are equal,
            i.e. orientations A = orientations B if there is a bijection between
            the orientations of A and B.
            -> FIXED kinda by not allowing this to happend in the first place

            TODO: Prune orientation maps to be non-overlapping.
            The intersection of the orientations of A and B is orientated with
            respect to the mask of A and B, and thus is a new orientation.
            The part of A not in B is a new orientation, and the part of B not
            in A is a new orientation.
            -> FIXED kinda by not allowing this to happend in the first place

            TODO: After splitting the orientations into non-overlapping parts,
            remove the orientations that are equivalent each other, i.e. the
            orientations that are a bijection between each other.
            -> FIXED kinda by not allowing this to happend in the first place
        """
        # Remove idx in orientation if in mask
        for pattern in self.patterns:
            pattern.orientations = [
                orientation * ~pattern.mask for orientation in pattern.orientations
            ]
        # Remove idx in orientation if in relative mask
        for pattern in self.patterns:
            if len(pattern.relative_masks) > 1:
                pattern.orientations = [
                    orientation * ~indices2mask(relative_mask[0], cube_size=pattern.size)
                    for orientation in pattern.orientations
                    for relative_mask in pattern.relative_masks
                ]
        # Remove idx in relative masks if in mask
        for pattern in self.patterns:
            new_relative_masks = []
            for relative_mask in pattern.relative_masks:
                new_relative_masks.append(
                    [
                        ordered_mask2indices(
                            indices2ordered_mask(indices, cube_size=pattern.size) * ~pattern.mask
                        )
                        for indices in relative_mask
                    ]
                )
            pattern.relative_masks = new_relative_masks


@lru_cache(maxsize=1)
def get_cubexes(cube_size: int = CUBE_SIZE) -> dict[str, CubexCollection]:
    """Return a dictionary of cube expressions from the tag.

    Args:
        cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.

    Returns:
        dict[str, CubexCollection]: Dictionary of cube expressions.
    """
    cubex_dict: dict[str, CubexCollection] = {}

    # Symmetric masks to discard
    mask_tags = {
        State.xp_face.value: "y",
        State.centers.value: "L R U D F B",
        State.line.value: "L R Uw",
    }
    for tag, string in mask_tags.items():
        cubex_dict[tag] = CubexCollection.from_solved_after_sequence(
            sequence=MoveSequence(string),
            keep=False,
            cube_size=cube_size,
        )

    # Symmetric masks
    mask_tags = {
        State.cp_layer.value: "M' S Dw",
        State.ep_layer.value: "M2 D2 F2 B2 Dw",
        State.layer.value: "Dw",
        State.cross.value: "R L U2 R2 L2 U2 R L U",
        State.f2l.value: "U",
        State.x_cross.value: "R L' U2 R2 L U2 R U",
        State.xx_cross_adjacent.value: "R L' U2 R' L U",
        State.xx_cross_diagonal.value: "R' L' U2 R L U",
        State.xxx_cross.value: "R U R' U",
        State.block_1x1x3.value: "Fw Rw",
        State.block_1x2x2.value: "U R Fw",
        State.block_1x2x3.value: "U Rw",
        State.block_2x2x2.value: "U R F",
        State.block_2x2x3.value: "U R",
        State.corners.value: "M' S E",
        State.edges.value: "E2 R L S2 L R' S2 R2 S M S M'",
        Progress.solved.value: "",
    }
    for tag, string in mask_tags.items():
        cubex_dict[tag] = CubexCollection.from_solved_after_sequence(
            sequence=MoveSequence(string),
            cube_size=cube_size,
        )

    # Symmetric relative solved masks
    cubex_dict[State.f2l_layer.value] = CubexCollection.from_relativly_solved(
        sequence=MoveSequence("Dw"),
        generator=MoveGenerator("<U>"),
        cube_size=cube_size,
    )

    # Symmetric corner orientations
    symmetric_corner_orientation_tags = {
        State.co_face.value: "<U>",
    }
    for tag, gen in symmetric_corner_orientation_tags.items():
        cubex_dict[tag] = CubexCollection.from_generator_orientation(
            pieces=[Piece.corner],
            generator=MoveGenerator(gen),
            cube_size=cube_size,
        )

    # Symmetric edge orientations
    symmetric_edge_orientation_tags = {
        State.eo_face.value: "<U>",
    }
    for tag, gen in symmetric_edge_orientation_tags.items():
        cubex_dict[tag] = CubexCollection.from_generator_orientation(
            pieces=[Piece.edge],
            generator=MoveGenerator(gen),
            cube_size=cube_size,
        )

    # Symmetric corner and edge orientations
    symmetric_edge_corner_orientation_tags = {
        State.face.value: "<U>",
    }
    for tag, gen in symmetric_edge_corner_orientation_tags.items():
        cubex_dict[tag] = CubexCollection.from_generator_orientation(
            pieces=[Piece.corner, Piece.edge],
            generator=MoveGenerator(gen),
            cube_size=cube_size,
        )

    # Symmetric composite
    cubex_dict[State.face.value] = cubex_dict[State.face.value] & cubex_dict[State.xp_face.value]
    cubex_dict[State.f2l_face.value] = cubex_dict[State.face.value] & cubex_dict[State.f2l.value]
    cubex_dict[State.f2l_layer.value] = (
        cubex_dict[State.f2l.value] & cubex_dict[State.f2l_layer.value]
    )
    cubex_dict[State.f2l_co.value] = cubex_dict[State.co_face.value] & cubex_dict[State.f2l.value]
    cubex_dict[State.f2l_eo.value] = cubex_dict[State.eo_face.value] & cubex_dict[State.f2l.value]
    cubex_dict[State.f2l_cp.value] = cubex_dict[State.cp_layer.value] & cubex_dict[State.f2l.value]
    cubex_dict[State.f2l_ep.value] = cubex_dict[State.ep_layer.value] & cubex_dict[State.f2l.value]
    cubex_dict[State.f2l_ep_co.value] = (
        cubex_dict[State.ep_layer.value] & cubex_dict[State.f2l_co.value]
    )
    cubex_dict[State.f2l_eo_cp.value] = (
        cubex_dict[State.eo_face.value] & cubex_dict[State.f2l_cp.value]
    )

    # Create symmetries for all cubexes defined above
    for name, cubex in cubex_dict.items():
        cubex.create_symmetries()

    # Non-symmetric masks
    mask_tags = {
        State.minus_slice_m.value: "M",
        State.minus_slice_s.value: "S",
        State.minus_slice_e.value: "E",
    }
    for tag, string in mask_tags.items():
        cubex_dict[tag] = CubexCollection.from_solved_after_sequence(
            sequence=MoveSequence(string),
            cube_size=cube_size,
        )

    # Non-symmetric relatice solved masks
    cubex_dict[State.floppy_fb_col.value] = CubexCollection.from_relativly_solved(
        sequence=MoveSequence("Dw Rw"),
        generator=MoveGenerator("<L2, R2, U2, D2>"),
        cube_size=cube_size,
    )
    cubex_dict[State.floppy_lr_col.value] = CubexCollection.from_relativly_solved(
        sequence=MoveSequence("Fw Dw"),
        generator=MoveGenerator("<F2, B2, U2, D2>"),
        cube_size=cube_size,
    )
    cubex_dict[State.floppy_ud_col.value] = CubexCollection.from_relativly_solved(
        sequence=MoveSequence("Fw Rw"),
        generator=MoveGenerator("<F2, B2, L2, R2>"),
        cube_size=cube_size,
    )

    # Non-symmetric edge orientations
    edge_orientation_tags = {
        State.eo_fb.value: "<F2, B2, L, R, U, D>",
        State.eo_lr.value: "<F, B, L2, R2 U, D>",
        State.eo_ud.value: "<F, B, L, R, U2, D2>",
        State.eo_fb_lr.value: "<F2, B2, L2, R2, U, D>",
        State.eo_fb_ud.value: "<F2, B2, L, R, U2, D2>",
        State.eo_lr_ud.value: "<F, B, L2, R2, U2, D2>",
        State.eo_floppy_fb.value: "<L2, R2, U2, D2>",
        State.eo_floppy_lr.value: "<F2, B2, U2, D2>",
        State.eo_floppy_ud.value: "<F2, B2, L2, R2>",
        State.eo_htr.value: "<F2, B2, L2, R2, U2, D2>",
    }
    for tag, gen in edge_orientation_tags.items():
        cubex_dict[tag] = CubexCollection.from_generator_orientation(
            pieces=[Piece.edge],
            generator=MoveGenerator(gen),
            cube_size=cube_size,
        )

    # Non-symmetric center orientations
    center_orientation_tags = {
        State.xo_fb.value: "z",
        State.xo_lr.value: "x",
        State.xo_ud.value: "y",
    }
    for tag, seq in center_orientation_tags.items():
        cubex_dict[tag] = CubexCollection.from_solved_after_sequence(
            sequence=MoveSequence(seq),
            invert=False,
            kind="orientation",
            keep=False,
            cube_size=cube_size,
        )

    # Non-symmetric corner orientations
    corner_orientation_tags = {
        State.co_fb.value: "<F, B, L2, R2, U2, D2>",
        State.co_lr.value: "<F2, B2, L, R, U2, D2>",
        State.co_ud.value: "<F2, B2, L2, R2, U, D>",
        State.co_htr.value: "<F2, B2, L2, R2, U2, D2>",
    }
    for tag, gen in corner_orientation_tags.items():
        cubex_dict[tag] = CubexCollection.from_generator_orientation(
            pieces=[Piece.corner],
            generator=MoveGenerator(gen),
            cube_size=cube_size,
        )

    # Non-symmetric corner and edge orientations

    # Composite patterns
    cubex_dict[State.eo.value] = (
        cubex_dict[State.eo_fb.value]
        | cubex_dict[State.eo_lr.value]
        | cubex_dict[State.eo_ud.value]
    )
    cubex_dict[State.co.value] = (
        cubex_dict[State.co_fb.value]
        | cubex_dict[State.co_lr.value]
        | cubex_dict[State.co_ud.value]
    )
    cubex_dict[State.xo_htr.value] = cubex_dict[State.xo_ud.value] & cubex_dict[State.xo_fb.value]
    cubex_dict[State.dr_ud.value] = (
        cubex_dict[State.co_ud.value]
        & cubex_dict[State.eo_fb_lr.value]
        & cubex_dict[State.xo_ud.value]
    )
    cubex_dict[State.dr_fb.value] = (
        cubex_dict[State.co_fb.value]
        & cubex_dict[State.eo_lr_ud.value]
        & cubex_dict[State.xo_fb.value]
    )
    cubex_dict[State.dr_lr.value] = (
        cubex_dict[State.co_lr.value]
        & cubex_dict[State.eo_fb_ud.value]
        & cubex_dict[State.xo_lr.value]
    )
    cubex_dict[State.dr.value] = (
        cubex_dict[State.dr_ud.value]
        | cubex_dict[State.dr_fb.value]
        | cubex_dict[State.dr_lr.value]
    )
    cubex_dict[State.floppy_fb.value] = (
        cubex_dict[State.floppy_fb_col.value]
        & cubex_dict[State.eo_floppy_fb.value]
        & cubex_dict[State.xo_htr.value]
    )
    cubex_dict[State.floppy_lr.value] = (
        cubex_dict[State.floppy_lr_col.value]
        & cubex_dict[State.eo_floppy_lr.value]
        & cubex_dict[State.xo_htr.value]
    )
    cubex_dict[State.floppy_ud.value] = (
        cubex_dict[State.floppy_ud_col.value]
        & cubex_dict[State.eo_floppy_ud.value]
        & cubex_dict[State.xo_htr.value]
    )
    cubex_dict[State.floppy.value] = (
        cubex_dict[State.floppy_fb.value]
        | cubex_dict[State.floppy_lr.value]
        | cubex_dict[State.floppy_ud.value]
    )
    cubex_dict[State.floppy_col.value] = (
        cubex_dict[State.floppy_fb_col.value]
        | cubex_dict[State.floppy_lr_col.value]
        | cubex_dict[State.floppy_ud_col.value]
    )
    cubex_dict[State.xx_cross.value] = (
        cubex_dict[State.xx_cross_adjacent.value] | cubex_dict[State.xx_cross_diagonal.value]
    )
    cubex_dict[State.minus_slice.value] = (
        cubex_dict[State.minus_slice_m.value]
        | cubex_dict[State.minus_slice_s.value]
        | cubex_dict[State.minus_slice_e.value]
    )
    cubex_dict[State.leave_slice_m.value] = (
        cubex_dict[State.minus_slice_m.value]
        & cubex_dict[State.eo_ud.value]
        & cubex_dict[State.xo_ud.value]
    )
    cubex_dict[State.leave_slice_s.value] = (
        cubex_dict[State.minus_slice_s.value]
        & cubex_dict[State.eo_lr.value]
        & cubex_dict[State.xo_lr.value]
    )
    cubex_dict[State.leave_slice_e.value] = (
        cubex_dict[State.minus_slice_e.value]
        & cubex_dict[State.eo_fb.value]
        & cubex_dict[State.xo_fb.value]
    )
    cubex_dict[State.leave_slice.value] = (
        cubex_dict[State.leave_slice_m.value]
        | cubex_dict[State.leave_slice_s.value]
        | cubex_dict[State.leave_slice_e.value]
    )
    cubex_dict[State.htr_like.value] = (
        cubex_dict[State.co_htr.value]
        & cubex_dict[State.eo_htr.value]
        & cubex_dict[State.xo_htr.value]
    )

    #    OPTIMIZE    #

    # Remove the cubexes that are not marked to keep
    to_delete = []
    for tag in cubex_dict.keys():
        if not cubex_dict[tag].keep:
            to_delete.append(tag)
    for tag in to_delete:
        del cubex_dict[tag]

    # Optimize the cubexes
    for cubex in cubex_dict.values():
        cubex.optimize()

    return sort_patterns(cubex_dict)


def sort_patterns(cubex_dict: dict[str, CubexCollection]) -> dict[str, CubexCollection]:
    """
    Sort the patterns by
    1. The number of patterns in the cubex.
    2. The maximum size of the mask.
    3. The maximum size of the oriented pieces.
    """

    # Sort by the number of patterns
    cubex_dict = dict(
        sorted(
            cubex_dict.items(),
            key=lambda cubex: len(cubex[1].patterns),
            reverse=True,
        ),
    )

    # Sort by the maximum size of the mask
    cubex_dict = dict(
        sorted(
            cubex_dict.items(),
            key=lambda cubex: max(sum(pattern.mask) for pattern in cubex[1].patterns),
            reverse=True,
        )
    )

    # Sort by the maximum size of the oriented pieces
    cubex_dict = dict(
        sorted(
            cubex_dict.items(),
            key=lambda cubex: max(
                sum(
                    reduce(
                        np.logical_or,  # type: ignore[arg-type]
                        [pattern.mask]
                        + pattern.orientations
                        + [
                            indices2mask(relative_mask[0], cube_size=pattern.size)
                            for relative_mask in pattern.relative_masks
                        ],
                    )
                )
                for pattern in cubex[1].patterns
            ),
            reverse=True,
        )
    )
    return cubex_dict
