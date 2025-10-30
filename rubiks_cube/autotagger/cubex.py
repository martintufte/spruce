from __future__ import annotations

import logging
import timeit
from functools import lru_cache
from math import log2
from typing import TYPE_CHECKING
from typing import Any

import numpy as np

from rubiks_cube.configuration import CUBE_SIZE
from rubiks_cube.configuration.enumeration import Pattern
from rubiks_cube.configuration.enumeration import Piece
from rubiks_cube.configuration.enumeration import Symmetry
from rubiks_cube.move.generator import MoveGenerator
from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.representation.mask import get_piece_mask
from rubiks_cube.representation.mask import get_rubiks_cube_mask
from rubiks_cube.representation.pattern import generate_pattern_symmetries_from_subset
from rubiks_cube.representation.pattern import get_empty_pattern
from rubiks_cube.representation.pattern import get_solved_pattern
from rubiks_cube.representation.pattern import merge_patterns
from rubiks_cube.representation.pattern import pattern_combinations
from rubiks_cube.representation.pattern import pattern_from_generator
from rubiks_cube.representation.pattern import pattern_implies

if TYPE_CHECKING:
    from rubiks_cube.configuration.types import CubePattern
    from rubiks_cube.configuration.types import CubePermutation


LOGGER = logging.getLogger(__name__)


class Cubex:
    patterns: list[CubePattern]
    names: list[str]
    _keep: bool
    _combinations: int | None = None
    _symmetry: Symmetry | None = None

    def __init__(
        self,
        patterns: list[CubePattern],
        names: list[str],
        symmetry: Symmetry | None = None,
        combinations: int | None = None,
        keep: bool = True,
    ) -> None:
        """
        Initialize the cube expression.

        Args:
            patterns (list[CubePattern]): List over patterns.
            names (list[str]): Names of the patterns.
            symmetry (Symmetry | None, optional): Symmetries. Defaults to None.
            combinations (int | None, optional): Number of combinations. Defaults to None.
            keep (bool, optional): Whether to keep the pattern. Defaults to True.
        """
        self.patterns = patterns
        self.names = names
        self._keep = keep
        self._combinations = combinations
        self._symmetry = symmetry

    def __repr__(self) -> str:
        return f"Cubex(patterns={self.patterns})"

    def __or__(self, other: Cubex) -> Cubex:
        return Cubex(
            patterns=[*self.patterns, *other.patterns],
            names=[*self.names, *other.names],
            keep=self._keep or other._keep,
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
            names=[f"{name}&{other_name}" for name in self.names for other_name in other.names],
            symmetry=self._symmetry or other._symmetry,
            keep=self._keep or other._keep,
        )

    def __rand__(self, other: Cubex) -> Cubex:
        return self & other

    def __contains__(self, other: Any) -> bool:
        if isinstance(other, Cubex):
            return any(
                pattern_implies(pattern, other_pattern)
                for pattern in self.patterns
                for other_pattern in other.patterns
            )
        return False

    def __len__(self) -> int:
        return len(self.patterns)

    def match(self, permutation: CubePermutation) -> bool:
        return any(np.array_equal(pattern[permutation], pattern) for pattern in self.patterns)

    @property
    def combinations(self) -> int:
        """Find the number of combinations for each pattern."""
        if self._combinations is None:
            self._combinations = sum(
                pattern_combinations(pattern, cube_size=CUBE_SIZE) for pattern in self.patterns
            )
        return self._combinations

    @property
    def entropy(self) -> float:
        """
        Find the estimated entropy of the patterns.

        This is the number of bits required to identify the permutation,
        given that at least one of the patterns is matched.
        The entropy of a single pattern is

            H(pattern) = -sum_{x in X} P[x] * log2(P[x]),

        where X is the set of all permutations where the pattern holds, and P[x] is the
        probability of the permutation x. Assuming a uniform probability, the entropy reduces to

            H(pattern) = log2(|X|).

        Returns:
            float: Estimated entropy of the patterns.

        """
        return log2(self.combinations)

    @classmethod
    def from_settings(
        cls,
        name: str,
        solved_sequence: MoveSequence | None = None,
        pieces: list[Piece] | None = None,
        piece_orientations: MoveGenerator | None = None,
        symmetry: Symmetry | None = None,
        keep: bool = True,
        cube_size: int = CUBE_SIZE,
    ) -> Cubex:
        """
        Cube expression from pieces that are solved after applying a sequence of moves.

        Args:
            name (str): Name of the cube expression.
            solved_sequence (MoveSequence, optional): Sequence for solved pieces.
            pieces (list[Piece], optional): List of pieces.
            piece_orientations (MoveGenerator, optional): Find conserved orientations of the pieces.
            symmetry (Symmetry, optional): Name of the specific symmetry to create subsets.
            keep (bool, optional): Whether to keep the pattern. Defaults to True.
            cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.

        Returns:
            Cubex: Cube expression.
        """
        # Find the solved pattern, the pieces that are solved after applying the sequence
        if solved_sequence is None:
            solved_pattern = get_empty_pattern(cube_size=cube_size)
        else:
            solved_mask = get_rubiks_cube_mask(sequence=solved_sequence, cube_size=cube_size)
            solved_pattern = get_solved_pattern(cube_size=cube_size)
            solved_pattern[~solved_mask] = 0

        # Find the orientations of the pieces given the generator
        if pieces is not None and piece_orientations is not None:
            piece_mask = get_piece_mask(
                piece=pieces,
                cube_size=cube_size,
            )
            orientations_pattern = pattern_from_generator(
                generator=piece_orientations,
                mask=piece_mask,
                cube_size=cube_size,
            )
            # Don't keep elements that appear only once
            unique, counts = np.unique(orientations_pattern, return_counts=True)
            mask = np.isin(orientations_pattern, unique[counts == 1])
            orientations_pattern[mask] = 0
        else:
            orientations_pattern = get_empty_pattern(cube_size=cube_size)

        return cls(
            patterns=[merge_patterns((solved_pattern, orientations_pattern))],
            names=[name],
            symmetry=symmetry,
            keep=keep,
        )

    def create_symmetries(self, cube_size: int = CUBE_SIZE) -> None:
        """Create symmetries for the cube expression."""
        if self._symmetry is None:
            return

        new_patterns = []
        new_names = []

        for pattern, _name in zip(self.patterns, self.names, strict=False):
            subset_patterns, subset_names = generate_pattern_symmetries_from_subset(
                pattern=pattern,
                symmetry=self._symmetry,
                prefix=self.names[0],
                cube_size=cube_size,
            )
            new_patterns.extend(subset_patterns)
            new_names.extend(subset_names)

        # Update the patterns and names
        self.patterns = new_patterns
        self.names = new_names


@lru_cache(maxsize=3)
def get_cubexes(cube_size: int = CUBE_SIZE) -> dict[str, Cubex]:
    """
    Return a dictionary of cube expressions for the cube size.

    Args:
        cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.

    Returns:
        dict[str, Cubex]: Dictionary of cube expressions.
    """
    t = timeit.default_timer()
    cubexes: dict[Pattern, Cubex] = {}

    seq: str
    symmetry: Symmetry | None
    solved_tags_discard = {
        Pattern.cp_layer: ("M' S Dw", Symmetry.up),
        Pattern.ep_layer: ("M2 D2 F2 B2 Dw", Symmetry.up),
        Pattern.none: ("x y", None),
    }
    for pattern, (seq, symmetry) in solved_tags_discard.items():
        cubexes[pattern] = Cubex.from_settings(
            name=pattern.value,
            solved_sequence=MoveSequence(seq),
            symmetry=symmetry,
            cube_size=cube_size,
            keep=False,
        )

    solved_tags = {
        Pattern.layer: ("Dw", Symmetry.up),
        Pattern.cross: ("R L U2 R2 L2 U2 R L U", Symmetry.down),
        Pattern.f2l: ("U", Symmetry.down),
        Pattern.x_cross: ("R L' U2 R2 L U2 R U", Symmetry.down_bl),
        Pattern.xx_cross_adjacent: ("R L' U2 R' L U", Symmetry.down_b),
        Pattern.xx_cross_diagonal: ("R' L' U2 R L U", Symmetry.down_bl_fr),
        Pattern.xxx_cross: ("R U R' U", Symmetry.down_fr),
        Pattern.block_1x1x3: ("Fw Rw", Symmetry.bl),
        Pattern.block_1x2x2: ("U R Fw", Symmetry.back_dl),
        Pattern.block_1x2x3: ("U Rw", Symmetry.dl),
        Pattern.block_2x2x2: ("U R F", Symmetry.down_bl),
        Pattern.block_2x2x3: ("U R", Symmetry.dl),
        Pattern.corners: ("M' S E", None),
        Pattern.edges: ("E2 R L S2 L R' S2 R2 S M S M'", None),
        Pattern.solved: ("", None),
        Pattern.minus_slice_m: ("M", None),
        Pattern.minus_slice_s: ("S", None),
        Pattern.minus_slice_e: ("E", None),
    }
    for pattern, (seq, symmetry) in solved_tags.items():
        cubexes[pattern] = Cubex.from_settings(
            name=pattern.value,
            solved_sequence=MoveSequence(seq),
            symmetry=symmetry,
            cube_size=cube_size,
        )

    # Symmetric orientations
    cubexes[Pattern.co_face] = Cubex.from_settings(
        name=Pattern.co_face.value,
        solved_sequence=MoveSequence("y"),
        pieces=[Piece.corner],
        piece_orientations=MoveGenerator("<U>"),
        symmetry=Symmetry.up,
        cube_size=cube_size,
    )
    cubexes[Pattern.eo_face] = Cubex.from_settings(
        name=Pattern.eo_face.value,
        solved_sequence=MoveSequence("y"),
        pieces=[Piece.edge],
        piece_orientations=MoveGenerator("<U>"),
        symmetry=Symmetry.up,
        cube_size=cube_size,
    )
    cubexes[Pattern.face] = Cubex.from_settings(
        name=Pattern.face.value,
        solved_sequence=MoveSequence("y"),
        pieces=[Piece.corner, Piece.edge],
        piece_orientations=MoveGenerator("<U>"),
        symmetry=Symmetry.up,
        cube_size=cube_size,
    )

    # Symmetric composite
    cubexes[Pattern.f2l_face] = cubexes[Pattern.face] & cubexes[Pattern.f2l]
    cubexes[Pattern.f2l_co] = cubexes[Pattern.co_face] & cubexes[Pattern.f2l]
    cubexes[Pattern.f2l_eo] = cubexes[Pattern.eo_face] & cubexes[Pattern.f2l]
    cubexes[Pattern.f2l_cp] = cubexes[Pattern.cp_layer] & cubexes[Pattern.f2l]
    cubexes[Pattern.f2l_ep] = cubexes[Pattern.ep_layer] & cubexes[Pattern.f2l]
    cubexes[Pattern.f2l_ep_co] = cubexes[Pattern.f2l_co] & cubexes[Pattern.ep_layer]
    cubexes[Pattern.f2l_eo_cp] = cubexes[Pattern.f2l_cp] & cubexes[Pattern.eo_face]

    # Create symmetries for all cubexes defined above
    for cubex in cubexes.values():
        cubex.create_symmetries(cube_size=cube_size)

    # Non-symmetric edge orientations
    edge_orientation_tags = {
        Pattern.eo_fb: "<F2, B2, L, R, U, D>",
        Pattern.eo_lr: "<F, B, L2, R2, U, D>",
        Pattern.eo_ud: "<F, B, L, R, U2, D2>",
        Pattern.eo_fb_lr: "<F2, B2, L2, R2, U, D>",
        Pattern.eo_fb_ud: "<F2, B2, L, R, U2, D2>",
        Pattern.eo_lr_ud: "<F, B, L2, R2, U2, D2>",
        Pattern.eo_floppy_fb: "<L2, R2, U2, D2>",
        Pattern.eo_floppy_lr: "<F2, B2, U2, D2>",
        Pattern.eo_floppy_ud: "<F2, B2, L2, R2>",
        Pattern.eo_htr: "<F2, B2, L2, R2, U2, D2>",
    }
    for pattern, gen in edge_orientation_tags.items():
        cubexes[pattern] = Cubex.from_settings(
            name=pattern.value,
            pieces=[Piece.edge],
            piece_orientations=MoveGenerator(gen),
            cube_size=cube_size,
        )

    # Non-symmetric center orientations
    center_orientation_tags = {
        Pattern.xo_fb: "z",
        Pattern.xo_lr: "x",
        Pattern.xo_ud: "y",
    }
    for pattern, seq in center_orientation_tags.items():
        cubexes[pattern] = Cubex.from_settings(
            name=pattern.value,
            solved_sequence=MoveSequence(seq),
            keep=False,
            cube_size=cube_size,
        )

    # Non-symmetric corner orientations
    corner_orientation_tags = {
        Pattern.co_fb: "<F, B, L2, R2, U2, D2>",
        Pattern.co_lr: "<F2, B2, L, R, U2, D2>",
        Pattern.co_ud: "<F2, B2, L2, R2, U, D>",
        Pattern.co_htr: "<F2, B2, L2, R2, U2, D2>",
    }
    for pattern, gen in corner_orientation_tags.items():
        cubexes[pattern] = Cubex.from_settings(
            name=pattern.value,
            pieces=[Piece.corner],
            piece_orientations=MoveGenerator(gen),
            cube_size=cube_size,
        )

    # Non-symmetric corner and edge orientations

    # Composite patterns
    cubexes[Pattern.xo_htr] = (
        cubexes[Pattern.xo_ud] & cubexes[Pattern.xo_lr] & cubexes[Pattern.xo_fb]
    )
    cubexes[Pattern.eo] = cubexes[Pattern.eo_fb] | cubexes[Pattern.eo_lr] | cubexes[Pattern.eo_ud]
    cubexes[Pattern.co] = cubexes[Pattern.co_fb] | cubexes[Pattern.co_lr] | cubexes[Pattern.co_ud]
    cubexes[Pattern.dr_ud] = (
        cubexes[Pattern.co_ud] & cubexes[Pattern.eo_fb_lr] & cubexes[Pattern.xo_htr]
    )
    cubexes[Pattern.dr_fb] = (
        cubexes[Pattern.co_fb] & cubexes[Pattern.eo_lr_ud] & cubexes[Pattern.xo_htr]
    )
    cubexes[Pattern.dr_lr] = (
        cubexes[Pattern.co_lr] & cubexes[Pattern.eo_fb_ud] & cubexes[Pattern.xo_htr]
    )
    cubexes[Pattern.dr] = cubexes[Pattern.dr_ud] | cubexes[Pattern.dr_fb] | cubexes[Pattern.dr_lr]
    cubexes[Pattern.xx_cross] = (
        cubexes[Pattern.xx_cross_adjacent] | cubexes[Pattern.xx_cross_diagonal]
    )
    cubexes[Pattern.minus_slice] = (
        cubexes[Pattern.minus_slice_m]
        | cubexes[Pattern.minus_slice_s]
        | cubexes[Pattern.minus_slice_e]
    )
    cubexes[Pattern.leave_slice_m] = (
        cubexes[Pattern.minus_slice_m] & cubexes[Pattern.eo_ud] & cubexes[Pattern.xo_ud]
    )
    cubexes[Pattern.leave_slice_s] = (
        cubexes[Pattern.minus_slice_s] & cubexes[Pattern.eo_lr] & cubexes[Pattern.xo_lr]
    )
    cubexes[Pattern.leave_slice_e] = (
        cubexes[Pattern.minus_slice_e] & cubexes[Pattern.eo_fb] & cubexes[Pattern.xo_fb]
    )
    cubexes[Pattern.leave_slice] = (
        cubexes[Pattern.leave_slice_m]
        | cubexes[Pattern.leave_slice_s]
        | cubexes[Pattern.leave_slice_e]
    )
    cubexes[Pattern.htr_like] = (
        cubexes[Pattern.co_htr] & cubexes[Pattern.eo_htr] & cubexes[Pattern.xo_htr]
    )

    for pattern in [pattern for pattern in cubexes if not cubexes[pattern]._keep]:
        del cubexes[pattern]
    LOGGER.debug(
        f"Created cubexes (size: {cube_size}) in {timeit.default_timer() - t:.2f} seconds."
    )

    t = timeit.default_timer()
    cubexes = {
        pattern: cubexes[pattern]
        for pattern in sorted(cubexes, key=lambda pattern: cubexes[pattern].entropy)
    }
    LOGGER.debug(f"Sorted cubexes in {timeit.default_timer() - t:.2f} seconds.")

    return {pattern.value: collection for pattern, collection in cubexes.items()}
