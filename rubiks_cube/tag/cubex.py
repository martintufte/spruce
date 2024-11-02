from __future__ import annotations

from functools import lru_cache
from math import log2
from typing import Any

import numpy as np

from rubiks_cube.configuration import CUBE_SIZE
from rubiks_cube.configuration.enumeration import Piece
from rubiks_cube.configuration.enumeration import Tag
from rubiks_cube.configuration.types import CubePattern
from rubiks_cube.configuration.types import CubePermutation
from rubiks_cube.move.generator import MoveGenerator
from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.state.mask import get_piece_mask
from rubiks_cube.state.mask import get_rubiks_cube_mask
from rubiks_cube.state.pattern import generate_symmetries
from rubiks_cube.state.pattern import get_empty_pattern
from rubiks_cube.state.pattern import get_solved_pattern
from rubiks_cube.state.pattern import merge_patterns
from rubiks_cube.state.pattern import pattern_combinations
from rubiks_cube.state.pattern import pattern_from_generator


class Cubex:
    patterns: list[CubePattern]
    combinations: list[int]
    keep: bool

    def __init__(
        self,
        patterns: list[CubePattern],
        combinations: list[int] | None = None,
        keep: bool = True,
    ) -> None:
        if combinations is None:
            combinations = [pattern_combinations(pattern) for pattern in patterns]
        self.patterns = patterns
        self.combinations = combinations
        self.keep = keep

    def __repr__(self) -> str:
        return f"Cubex(patterns={self.patterns}, combinations={self.combinations})"

    def __or__(self, other: Cubex) -> Cubex:
        return Cubex(
            patterns=[*self.patterns, *other.patterns],
            combinations=self.combinations + other.combinations,
            keep=self.keep or other.keep,
        )

    def __ror__(self, other: Cubex) -> Cubex:
        return self | other

    def __and__(self, other: Cubex) -> Cubex:
        return Cubex(
            patterns=[
                merge_patterns((pattern, other_pattern))
                for pattern in self.patterns
                for other_pattern in other.patterns
            ],
            keep=self.keep or other.keep,
        )

    def __rand__(self, other: Cubex) -> Cubex:
        return self & other

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Cubex):
            return self.patterns == other.patterns
        return False

    def __len__(self) -> int:
        return len(self.patterns)

    def match(self, permutation: CubePermutation) -> bool:
        return any(np.array_equal(pattern[permutation], pattern) for pattern in self.patterns)

    @property
    def entropy(self) -> float:
        return estimated_entropy(self)

    @classmethod
    def from_settings(
        cls,
        mask_sequence: MoveSequence | None = None,
        pieces: list[str] | None = None,
        generator: MoveGenerator | None = None,
        keep: bool = True,
        cube_size: int = CUBE_SIZE,
    ) -> Cubex:
        """Cube expression from pieces that are solved after applying a sequence of moves.

        Args:
            sequence (MoveSequence, optional): Move sequence for solved pieces. Defaults to None.
            pieces (list[str], optional): List of pieces. Defaults to None.
            generator (MoveGenerator, optional): Move generator. Defaults to None.
            keep (bool, optional): Wether to keep the pattern. Defaults to True.
            cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.

        Returns:
            Cubex: Cube expression.
        """
        if mask_sequence is None:
            solved_pattern = get_empty_pattern(cube_size=cube_size)
        else:
            solved_mask = get_rubiks_cube_mask(sequence=mask_sequence, cube_size=cube_size)
            solved_pattern = get_solved_pattern(cube_size=cube_size)
            solved_pattern[~solved_mask] = 0

        if pieces is None or generator is None:
            generator_pattern = get_empty_pattern(cube_size=cube_size)
        else:
            piece_map = {
                "corner": Piece.corner,
                "edge": Piece.edge,
                "center": Piece.center,
            }
            generator_pattern = pattern_from_generator(
                generator=generator,
                mask=get_piece_mask(
                    piece=[piece_map[piece] for piece in pieces],
                    cube_size=cube_size,
                ),
                cube_size=cube_size,
            )

        return cls(patterns=[merge_patterns((solved_pattern, generator_pattern))], keep=keep)

    def create_symmetries(self) -> None:
        """Create symmetries for the cube expression."""
        new_patterns = []
        for pattern in self.patterns:
            new_patterns.extend(generate_symmetries(pattern))
        self.patterns = new_patterns


@lru_cache(maxsize=1)
def get_cubexes(cube_size: int = CUBE_SIZE) -> dict[str, Cubex]:
    """Return a dictionary of cube expressions from the tag.

    Args:
        cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.

    Returns:
        dict[Tag, Cubex]: Dictionary of cube expressions.
    """
    cubexes: dict[Tag, Cubex] = {}

    # Symmetric masks to discard
    mask_tags = {
        Tag.xp_face: "y",
        Tag.centers: "L R U D F B",
        Tag.line: "L R Uw",
    }
    for tag, string in mask_tags.items():
        cubexes[tag] = Cubex.from_settings(
            mask_sequence=MoveSequence(string),
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
        cubexes[tag] = Cubex.from_settings(
            mask_sequence=MoveSequence(string),
            cube_size=cube_size,
        )

    # Symmetric corner orientations
    symmetric_corner_orientation_tags = {
        Tag.co_face: "<U>",
    }
    for tag, gen in symmetric_corner_orientation_tags.items():
        cubexes[tag] = Cubex.from_settings(
            pieces=[Piece.corner.value],
            generator=MoveGenerator(gen),
            cube_size=cube_size,
        )

    # Symmetric edge orientations
    symmetric_edge_orientation_tags = {
        Tag.eo_face: "<U>",
    }
    for tag, gen in symmetric_edge_orientation_tags.items():
        cubexes[tag] = Cubex.from_settings(
            pieces=[Piece.edge.value],
            generator=MoveGenerator(gen),
            cube_size=cube_size,
        )

    # Symmetric corner and edge orientations
    symmetric_edge_corner_orientation_tags = {
        Tag.face: "<U>",
    }
    for tag, gen in symmetric_edge_corner_orientation_tags.items():
        cubexes[tag] = Cubex.from_settings(
            pieces=[Piece.corner.value, Piece.edge.value],
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
        cubexes[tag] = Cubex.from_settings(
            mask_sequence=MoveSequence(string),
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
        cubexes[tag] = Cubex.from_settings(
            mask_sequence=None,
            pieces=[Piece.edge.value],
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
        cubexes[tag] = Cubex.from_settings(
            mask_sequence=MoveSequence(seq),
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
        cubexes[tag] = Cubex.from_settings(
            pieces=[Piece.corner.value],
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

    # Sort the cubexes by their entropy (equiv. to the number of combinations)
    cubexes = {
        tag: cubexes[tag] for tag in sorted(cubexes, key=lambda tag: cubexes[tag].combinations)
    }

    return {tag.value: collection for tag, collection in cubexes.items()}


def estimated_entropy(cubex: Cubex) -> float:
    """Return the entropy of the Cubex.

    Args:
        cubex (Cubex): Cube expression.

    Returns:
        float: Estimated entropy of the patterns. This is the number of bits required to identify
            the permutation, given that at least one of the patterns is matched. The entropy of a
            single pattern is
                H(pattern) = -sum_{x in X} P[x] * log2(P[x]),
            where X is the set of all permutations where the pattern holds, and P[x] is the
            probability of the permutation x. Assuming a uniform propability, the entropy reduces to
                H(pattern) = log2(|X|).
            The entropy of the Cubex is estimated by summing the number of states of the patterns.
                H(cubex) ~ log2(|X|) = log2( sum_{pattern in Cubex} |patterns| ).
    """
    return log2(sum(cubex.combinations))
