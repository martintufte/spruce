from __future__ import annotations

from functools import lru_cache
from typing import Any

import numpy as np

from rubiks_cube.configuration import CUBE_SIZE
from rubiks_cube.configuration.enumeration import Piece
from rubiks_cube.configuration.enumeration import Tag
from rubiks_cube.configuration.type_definitions import CubeMask
from rubiks_cube.configuration.type_definitions import CubePattern
from rubiks_cube.configuration.type_definitions import CubePermutation
from rubiks_cube.move.generator import MoveGenerator
from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.state import get_rubiks_cube_state
from rubiks_cube.state.mask import get_piece_mask
from rubiks_cube.state.mask import get_rubiks_cube_mask
from rubiks_cube.state.mask import get_zeros_mask
from rubiks_cube.state.pattern import generate_symmetries
from rubiks_cube.state.pattern import pattern_from_generator
from rubiks_cube.state.permutation import get_identity_permutation


class Cubex:
    mask: CubeMask
    pattern: CubePattern | None
    cube_size: int

    def __init__(
        self,
        mask: CubeMask | None = None,
        pattern: CubePattern | None = None,
        cube_size: int = CUBE_SIZE,
    ) -> None:
        """Initialize the cube expression.

        Args:
            mask (CubeMask, optional): Mask of pieces that must be solved. Defaults to None.
            pattern (CubePattern, optional): Pattern on the rest of the cube. Defaults to None.
            cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.
        """
        self.mask = get_zeros_mask(cube_size=cube_size) if mask is None else mask
        self.pattern = pattern
        self.cube_size = cube_size

    def __repr__(self) -> str:
        mask_repr = str(self.mask) if np.any(self.mask) else "None"
        return f"Cubex(mask={mask_repr}, pattern={self.pattern}), cube_size={self.cube_size})"

    def _match_mask(self, permutation: CubePermutation, goal: CubePermutation) -> bool:
        return np.array_equal(permutation[self.mask], goal[self.mask])

    def _match_pattern(self, permutation: CubePermutation, goal: CubePermutation) -> bool:
        if self.pattern is None:
            return True
        return np.array_equal(self.pattern[permutation], self.pattern[goal])

    def match(self, permutation: CubePermutation, goal: CubePermutation) -> bool:
        return self._match_mask(permutation, goal) and self._match_pattern(permutation, goal)

    def __and__(self, other: Cubex) -> Cubex:
        return Cubex(
            mask=self.mask | other.mask,
            pattern=None,
            cube_size=self.cube_size,
        )

    def __rand__(self, other: Cubex) -> Cubex:
        return self & other

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Cubex):
            return hash(self) == hash(other)
        return False

    def __hash__(self) -> int:
        if self.pattern is None:
            return hash((self.mask.tobytes(), self.cube_size))
        return hash((self.mask.tobytes(), self.pattern.tobytes(), self.cube_size))

    def create_symmetries(self) -> list[Cubex]:
        """Create all symmetries that matches the cubex."""
        pattern = np.zeros(self.mask.size, dtype=int) if self.pattern is None else self.pattern

        symmetries = generate_symmetries(
            patterns=(self.mask, pattern),
            cube_size=self.cube_size,
        )

        if self.pattern is not None:
            return [
                Cubex(mask=symmetry[0], pattern=symmetry[1], cube_size=self.cube_size)
                for symmetry in symmetries
            ]
        return [
            Cubex(mask=symmetry[0], pattern=None, cube_size=self.cube_size)
            for symmetry in symmetries
        ]


class CubexCollection:
    """Cube Expression Collection."""

    def __init__(self, cubexes: list[Cubex], keep: bool = True) -> None:
        """Initialize the cube expression.

        Args:
            cubexes (list[Cubex]): List of cube expressions.
            keep (bool, optional): Whether to keep the pattern. Defaults to True.
        """
        self.cubexes = list(set(cubexes))
        self.keep = keep

    def __repr__(self) -> str:
        return f"CubexCollection(cubexes={self.cubexes})"

    def __or__(self, other: CubexCollection) -> CubexCollection:
        return CubexCollection(
            cubexes=[*self.cubexes, *other.cubexes], keep=self.keep or other.keep
        )

    def __ror__(self, other: CubexCollection) -> CubexCollection:
        return self | other

    def __and__(self, other: CubexCollection) -> CubexCollection:
        return CubexCollection(
            cubexes=[
                cubex & other_cubex for cubex in self.cubexes for other_cubex in other.cubexes
            ],
            keep=self.keep or other.keep,
        )

    def __rand__(self, other: CubexCollection) -> CubexCollection:
        return self & other

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, CubexCollection):
            return self.cubexes == other.cubexes
        return False

    def __len__(self) -> int:
        return len(self.cubexes)

    def match(self, input: MoveSequence | CubePermutation, cube_size: int = CUBE_SIZE) -> bool:
        """Check if the permutation matches any of the patterns.

        Args:
            input (MoveSequence | CubePermutation): Input to check.
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
        return any(cubex.match(permutation, goal=goal) for cubex in self.cubexes)

    @classmethod
    def from_solved_mask(
        cls,
        sequence: MoveSequence = MoveSequence(),
        invert: bool = False,
        keep: bool = True,
        cube_size: int = CUBE_SIZE,
    ) -> CubexCollection:
        """Cube expression from pieces that are solved after applying a sequence of moves.

        Args:
            sequence (MoveSequence, optional): Move sequence. Defaults to MoveSequence().
            invert (bool, optional): Wether to invert afterwards. Defaults to False.
            keep (bool, optional): Wether to keep the pattern. Defaults to True.
            cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.

        Returns:
            CubexCollection: Cube expression.
        """
        mask = get_rubiks_cube_mask(sequence=sequence, invert=invert, cube_size=cube_size)
        return cls([Cubex(mask=mask, cube_size=cube_size)], keep=keep)

    @classmethod
    def from_generator(
        cls,
        pieces: list[Piece],
        generator: MoveGenerator,
        keep: bool = True,
        cube_size: int = CUBE_SIZE,
    ) -> CubexCollection:
        """Create a cube expression from the orientation that is perserved
        in the generator.

        Args:
            pieces (list[Piece]): List of pieces.
            generator (MoveGenerator): Move generator.
            keep (bool, optional): Wether to keep the pattern. Defaults to True.
            cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.

        Returns:
            CubexCollection: Cube expression.
        """
        mask = get_piece_mask(piece=pieces, cube_size=cube_size)

        pattern = pattern_from_generator(
            generator=generator,
            mask=mask,
            cube_size=cube_size,
        )

        return cls([Cubex(mask=None, pattern=pattern, cube_size=cube_size)], keep=keep)

    def create_symmetries(self) -> None:
        """Create symmetries for the cube expression only if it has a mask."""
        new_cubexes = []
        for cubex in self.cubexes:
            new_cubexes.extend(cubex.create_symmetries())
        self.cubexes = new_cubexes

    def optimize(self) -> None:
        pass


@lru_cache(maxsize=1)
def get_cubexes(cube_size: int = CUBE_SIZE) -> dict[Tag, CubexCollection]:
    """Return a dictionary of cube expressions from the tag.

    Args:
        cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.

    Returns:
        dict[Tag, CubexCollection]: Dictionary of cube expressions.
    """
    cubexes: dict[Tag, CubexCollection] = {}

    # Symmetric masks to discard
    mask_tags = {
        Tag.xp_face: "y",
        Tag.centers: "L R U D F B",
        Tag.line: "L R Uw",
    }
    for tag, string in mask_tags.items():
        cubexes[tag] = CubexCollection.from_solved_mask(
            sequence=MoveSequence(string),
            keep=False,
            cube_size=cube_size,
        )

    # Symmetric masks
    mask_tags = {
        Tag.cp_layer: "M' S Dw",
        Tag.ep_layer: "M2 D2 F2 B2 Dw",
        Tag.layer: "Dw",
        Tag.cross: "R L U2 R2 L2 U2 R L U",
        Tag.f2l: "U",
        Tag.x_cross: "R L' U2 R2 L U2 R U",
        Tag.xx_cross_adjacent: "R L' U2 R' L U",
        Tag.xx_cross_diagonal: "R' L' U2 R L U",
        Tag.xxx_cross: "R U R' U",
        Tag.block_1x1x3: "Fw Rw",
        Tag.block_1x2x2: "U R Fw",
        Tag.block_1x2x3: "U Rw",
        Tag.block_2x2x2: "U R F",
        Tag.block_2x2x3: "U R",
        Tag.corners: "M' S E",
        Tag.edges: "E2 R L S2 L R' S2 R2 S M S M'",
        Tag.solved: "",
    }
    for tag, string in mask_tags.items():
        cubexes[tag] = CubexCollection.from_solved_mask(
            sequence=MoveSequence(string),
            cube_size=cube_size,
        )

    # Symmetric corner orientations
    symmetric_corner_orientation_tags = {
        Tag.co_face: "<U>",
    }
    for tag, gen in symmetric_corner_orientation_tags.items():
        cubexes[tag] = CubexCollection.from_generator(
            pieces=[Piece.corner],
            generator=MoveGenerator(gen),
            cube_size=cube_size,
        )

    # Symmetric edge orientations
    symmetric_edge_orientation_tags = {
        Tag.eo_face: "<U>",
    }
    for tag, gen in symmetric_edge_orientation_tags.items():
        cubexes[tag] = CubexCollection.from_generator(
            pieces=[Piece.edge],
            generator=MoveGenerator(gen),
            cube_size=cube_size,
        )

    # Symmetric corner and edge orientations
    symmetric_edge_corner_orientation_tags = {
        Tag.face: "<U>",
    }
    for tag, gen in symmetric_edge_corner_orientation_tags.items():
        cubexes[tag] = CubexCollection.from_generator(
            pieces=[Piece.corner, Piece.edge],
            generator=MoveGenerator(gen),
            cube_size=cube_size,
        )

    # Symmetric composite
    cubexes[Tag.face] = cubexes[Tag.face] & cubexes[Tag.xp_face]
    cubexes[Tag.f2l_face] = cubexes[Tag.face] & cubexes[Tag.f2l]
    cubexes[Tag.f2l_co] = cubexes[Tag.co_face] & cubexes[Tag.f2l]
    cubexes[Tag.f2l_eo] = cubexes[Tag.eo_face] & cubexes[Tag.f2l]
    cubexes[Tag.f2l_cp] = cubexes[Tag.cp_layer] & cubexes[Tag.f2l]
    cubexes[Tag.f2l_ep] = cubexes[Tag.ep_layer] & cubexes[Tag.f2l]
    cubexes[Tag.f2l_ep_co] = cubexes[Tag.ep_layer] & cubexes[Tag.f2l_co]
    cubexes[Tag.f2l_eo_cp] = cubexes[Tag.eo_face] & cubexes[Tag.f2l_cp]

    # Create symmetries for all cubexes defined above
    for tag, cubex in cubexes.items():
        cubex.create_symmetries()

    # Non-symmetric tags
    mask_tags = {
        Tag.minus_slice_m: "M",
        Tag.minus_slice_s: "S",
        Tag.minus_slice_e: "E",
    }
    for tag, string in mask_tags.items():
        cubexes[tag] = CubexCollection.from_solved_mask(
            sequence=MoveSequence(string),
            cube_size=cube_size,
        )

    # Non-symmetric edge orientations
    edge_orientation_tags = {
        Tag.eo_fb: "<F2, B2, L, R, U, D>",
        Tag.eo_lr: "<F, B, L2, R2 U, D>",
        Tag.eo_ud: "<F, B, L, R, U2, D2>",
        Tag.eo_fb_lr: "<F2, B2, L2, R2, U, D>",
        Tag.eo_fb_ud: "<F2, B2, L, R, U2, D2>",
        Tag.eo_lr_ud: "<F, B, L2, R2, U2, D2>",
        Tag.eo_floppy_fb: "<L2, R2, U2, D2>",
        Tag.eo_floppy_lr: "<F2, B2, U2, D2>",
        Tag.eo_floppy_ud: "<F2, B2, L2, R2>",
        Tag.eo_htr: "<F2, B2, L2, R2, U2, D2>",
    }
    for tag, gen in edge_orientation_tags.items():
        cubexes[tag] = CubexCollection.from_generator(
            pieces=[Piece.edge],
            generator=MoveGenerator(gen),
            cube_size=cube_size,
        )

    # Non-symmetric center orientations
    center_orientation_tags = {
        Tag.xo_fb: "z",
        Tag.xo_lr: "x",
        Tag.xo_ud: "y",
    }
    for tag, seq in center_orientation_tags.items():
        cubexes[tag] = CubexCollection.from_solved_mask(
            sequence=MoveSequence(seq),
            invert=False,
            keep=False,
            cube_size=cube_size,
        )

    # Non-symmetric corner orientations
    corner_orientation_tags = {
        Tag.co_fb: "<F, B, L2, R2, U2, D2>",
        Tag.co_lr: "<F2, B2, L, R, U2, D2>",
        Tag.co_ud: "<F2, B2, L2, R2, U, D>",
        Tag.co_htr: "<F2, B2, L2, R2, U2, D2>",
    }
    for tag, gen in corner_orientation_tags.items():
        cubexes[tag] = CubexCollection.from_generator(
            pieces=[Piece.corner],
            generator=MoveGenerator(gen),
            cube_size=cube_size,
        )

    # Non-symmetric corner and edge orientations

    # Composite patterns
    cubexes[Tag.eo] = cubexes[Tag.eo_fb] | cubexes[Tag.eo_lr] | cubexes[Tag.eo_ud]
    cubexes[Tag.co] = cubexes[Tag.co_fb] | cubexes[Tag.co_lr] | cubexes[Tag.co_ud]
    cubexes[Tag.xo_htr] = cubexes[Tag.xo_ud] & cubexes[Tag.xo_fb]
    cubexes[Tag.dr_ud] = cubexes[Tag.co_ud] & cubexes[Tag.eo_fb_lr] & cubexes[Tag.xo_ud]
    cubexes[Tag.dr_fb] = cubexes[Tag.co_fb] & cubexes[Tag.eo_lr_ud] & cubexes[Tag.xo_fb]
    cubexes[Tag.dr_lr] = cubexes[Tag.co_lr] & cubexes[Tag.eo_fb_ud] & cubexes[Tag.xo_lr]
    cubexes[Tag.dr] = cubexes[Tag.dr_ud] | cubexes[Tag.dr_fb] | cubexes[Tag.dr_lr]
    cubexes[Tag.xx_cross] = cubexes[Tag.xx_cross_adjacent] | cubexes[Tag.xx_cross_diagonal]
    cubexes[Tag.minus_slice] = (
        cubexes[Tag.minus_slice_m] | cubexes[Tag.minus_slice_s] | cubexes[Tag.minus_slice_e]
    )
    cubexes[Tag.leave_slice_m] = (
        cubexes[Tag.minus_slice_m] & cubexes[Tag.eo_ud] & cubexes[Tag.xo_ud]
    )
    cubexes[Tag.leave_slice_s] = (
        cubexes[Tag.minus_slice_s] & cubexes[Tag.eo_lr] & cubexes[Tag.xo_lr]
    )
    cubexes[Tag.leave_slice_e] = (
        cubexes[Tag.minus_slice_e] & cubexes[Tag.eo_fb] & cubexes[Tag.xo_fb]
    )
    cubexes[Tag.leave_slice] = (
        cubexes[Tag.leave_slice_m] | cubexes[Tag.leave_slice_s] | cubexes[Tag.leave_slice_e]
    )
    cubexes[Tag.htr_like] = cubexes[Tag.co_htr] & cubexes[Tag.eo_htr] & cubexes[Tag.xo_htr]

    # Remove the cubexes that are not marked to keep
    to_delete = []
    for tag in cubexes.keys():
        if not cubexes[tag].keep:
            to_delete.append(tag)
    for tag in to_delete:
        del cubexes[tag]

    for cubex in cubexes.values():
        cubex.optimize()

    return cubexes
