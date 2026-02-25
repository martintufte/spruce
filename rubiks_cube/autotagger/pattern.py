from __future__ import annotations

import logging
import timeit
from functools import cached_property
from functools import lru_cache
from math import log2
from typing import TYPE_CHECKING
from typing import Any
from typing import Self  # ty: ignore[unresolved-import]

import attrs
import numpy as np

from rubiks_cube.configuration import CUBE_SIZE
from rubiks_cube.configuration.enumeration import Goal
from rubiks_cube.configuration.enumeration import Piece
from rubiks_cube.configuration.enumeration import Symmetry
from rubiks_cube.move.generator import MoveGenerator
from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.representation.mask import get_piece_mask
from rubiks_cube.representation.mask import get_rubiks_cube_mask
from rubiks_cube.representation.pattern import generate_pattern_symmetries_from_subset
from rubiks_cube.representation.pattern import get_empty_pattern
from rubiks_cube.representation.pattern import get_identity_pattern
from rubiks_cube.representation.pattern import merge_patterns
from rubiks_cube.representation.pattern import pattern_combinations
from rubiks_cube.representation.pattern import pattern_from_generator
from rubiks_cube.representation.pattern import pattern_implies

if TYPE_CHECKING:
    from rubiks_cube.configuration.types import CubePattern
    from rubiks_cube.configuration.types import CubePermutation


LOGGER = logging.getLogger(__name__)


@attrs.mutable
class Pattern:
    patterns: list[CubePattern]
    names: list[str]
    symmetry: Symmetry = Symmetry.none
    keep: bool = True

    @classmethod
    def from_settings(
        cls,
        name: str,
        solved_sequence: MoveSequence | None = None,
        pieces: list[Piece] | None = None,
        piece_orientations: MoveGenerator | None = None,
        symmetry: Symmetry = Symmetry.none,
        keep: bool = True,
        cube_size: int = CUBE_SIZE,
    ) -> Self:
        """Cube expression from pieces that are solved after applying a sequence of moves.

        Args:
            name (str): Name of the cube expression.
            solved_sequence (MoveSequence, optional): Sequence for solved pieces.
            pieces (list[Piece], optional): List of pieces.
            piece_orientations (MoveGenerator, optional): Find conserved orientations of the pieces.
            symmetry (Symmetry, optional): Specific symmetry for creating variations.
                Defaults to Symmetry.none.
            keep (bool, optional): Whether to keep the pattern. Defaults to True.
            cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.

        Returns:
            Self: Cube expression.
        """
        # Find the solved pattern, the pieces that are solved after applying the sequence
        if solved_sequence is None:
            solved_pattern = get_empty_pattern(cube_size=cube_size)
        else:
            solved_mask = get_rubiks_cube_mask(sequence=solved_sequence, cube_size=cube_size)
            solved_pattern = get_identity_pattern(cube_size=cube_size)
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

    def __or__(self, other: Pattern) -> Pattern:
        return Pattern(
            patterns=[*self.patterns, *other.patterns],
            names=[*self.names, *other.names],
            symmetry=Symmetry.none,
            keep=self.keep or other.keep,
        )

    def __ror__(self, other: Pattern) -> Pattern:
        return self | other

    def __and__(self, other: Pattern) -> Pattern:
        return Pattern(
            patterns=[
                merge_patterns((pattern, other_pattern))
                for pattern in self.patterns
                for other_pattern in other.patterns
            ],
            names=[f"{name}&{other_name}" for name in self.names for other_name in other.names],
            symmetry=self.symmetry or other.symmetry,
            keep=self.keep or other.keep,
        )

    def __rand__(self, other: Pattern) -> Pattern:
        return self & other

    def __contains__(self, other: Any) -> bool:
        if isinstance(other, Pattern):
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

    @cached_property
    def combinations(self) -> int:
        """Sum of the number of combinations for each pattern."""
        return sum(pattern_combinations(pattern, cube_size=CUBE_SIZE) for pattern in self.patterns)

    @property
    def entropy(self) -> float:
        """Find the estimated entropy of the patterns.

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

    def create_symmetries(self, cube_size: int = CUBE_SIZE) -> None:
        """Create symmetries for the cube expression."""
        if self.symmetry is Symmetry.none:
            return

        new_patterns = []
        new_names = []

        for pattern, _name in zip(self.patterns, self.names, strict=False):
            subset_patterns, subset_names = generate_pattern_symmetries_from_subset(
                pattern=pattern,
                symmetry=self.symmetry,
                prefix=self.names[0],
                cube_size=cube_size,
            )
            new_patterns.extend(subset_patterns)
            new_names.extend(subset_names)

        # Update the patterns and names
        self.patterns = new_patterns
        self.names = new_names


@lru_cache(maxsize=3)
def get_patterns(cube_size: int = CUBE_SIZE) -> dict[Goal, Pattern]:
    """Return a dictionary of cube expressions for the cube size.

    Args:
        cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.

    Returns:
        dict[str, Pattern]: Dictionary of goals with their patterns.
    """
    t = timeit.default_timer()
    patterns: dict[Goal, Pattern] = {}

    solved_tags_discard = {
        Goal.cp_layer: (["M'", "S", "Dw"], Symmetry.up),
        Goal.ep_layer: (["M2", "D2", "F2", "B2", "Dw"], Symmetry.up),
        Goal.none: (["x", "y"], Symmetry.none),
    }
    for goal, (moves, symmetry) in solved_tags_discard.items():
        patterns[goal] = Pattern.from_settings(
            name=goal.value,
            solved_sequence=MoveSequence(moves),
            symmetry=symmetry,
            cube_size=cube_size,
            keep=False,
        )

    solved_tags = {
        Goal.layer: (["Dw"], Symmetry.up),
        Goal.cross: (["R", "L", "U2", "R2", "L2", "U2", "R", "L", "U"], Symmetry.down),
        Goal.f2l: (["U"], Symmetry.down),
        Goal.x_cross: (["R", "L'", "U2", "R2", "L", "U2", "R", "U"], Symmetry.down_bl),
        Goal.xx_cross_adjacent: (["R", "L'", "U2", "R'", "L", "U"], Symmetry.down_b),
        Goal.xx_cross_diagonal: (["R'", "L'", "U2", "R", "L", "U"], Symmetry.down_bl_fr),
        Goal.xxx_cross: (["R", "U", "R'", "U"], Symmetry.down_fr),
        Goal.block_1x1x3: (["Fw", "Rw"], Symmetry.bl),
        Goal.block_1x2x2: (["U", "R", "Fw"], Symmetry.back_dl),
        Goal.block_1x2x3: (["U", "Rw"], Symmetry.dl),
        Goal.block_2x2x2: (["U", "R", "F"], Symmetry.down_bl),
        Goal.block_2x2x3: (["U", "R"], Symmetry.dl),
        Goal.corners: (["M'", "S", "E"], Symmetry.none),
        Goal.edges: (
            ["E2", "R", "L", "S2", "L", "R'", "S2", "R2", "S", "M", "S", "M'"],
            Symmetry.none,
        ),
        Goal.solved: ([], Symmetry.none),
        Goal.minus_slice_m: (["M"], Symmetry.none),
        Goal.minus_slice_s: (["S"], Symmetry.none),
        Goal.minus_slice_e: (["E"], Symmetry.none),
    }
    for goal, (moves, symmetry) in solved_tags.items():
        patterns[goal] = Pattern.from_settings(
            name=goal.value,
            solved_sequence=MoveSequence(moves),
            symmetry=symmetry,
            cube_size=cube_size,
        )

    # Symmetric orientations
    patterns[Goal.co_face] = Pattern.from_settings(
        name=Goal.co_face.value,
        solved_sequence=MoveSequence(["y"]),
        pieces=[Piece.corner],
        piece_orientations=MoveGenerator.from_str("<U>"),
        symmetry=Symmetry.up,
        cube_size=cube_size,
    )
    patterns[Goal.eo_face] = Pattern.from_settings(
        name=Goal.eo_face.value,
        solved_sequence=MoveSequence(["y"]),
        pieces=[Piece.edge],
        piece_orientations=MoveGenerator.from_str("<U>"),
        symmetry=Symmetry.up,
        cube_size=cube_size,
    )
    patterns[Goal.face] = Pattern.from_settings(
        name=Goal.face.value,
        solved_sequence=MoveSequence(["y"]),
        pieces=[Piece.corner, Piece.edge],
        piece_orientations=MoveGenerator.from_str("<U>"),
        symmetry=Symmetry.up,
        cube_size=cube_size,
    )

    # Symmetric composite
    patterns[Goal.f2l_face] = patterns[Goal.face] & patterns[Goal.f2l]
    patterns[Goal.f2l_co] = patterns[Goal.co_face] & patterns[Goal.f2l]
    patterns[Goal.f2l_eo] = patterns[Goal.eo_face] & patterns[Goal.f2l]
    patterns[Goal.f2l_cp] = patterns[Goal.cp_layer] & patterns[Goal.f2l]
    patterns[Goal.f2l_ep] = patterns[Goal.ep_layer] & patterns[Goal.f2l]
    patterns[Goal.f2l_ep_co] = patterns[Goal.f2l_co] & patterns[Goal.ep_layer]
    patterns[Goal.f2l_eo_cp] = patterns[Goal.f2l_cp] & patterns[Goal.eo_face]

    # Create symmetries for all patterns defined above
    for pattern in patterns.values():
        pattern.create_symmetries(cube_size=cube_size)

    # Non-symmetric edge orientations
    edge_orientation_tags = {
        Goal.eo_fb: "<F2, B2, L, R, U, D>",
        Goal.eo_lr: "<F, B, L2, R2, U, D>",
        Goal.eo_ud: "<F, B, L, R, U2, D2>",
        Goal.eo_fb_lr: "<F2, B2, L2, R2, U, D>",
        Goal.eo_fb_ud: "<F2, B2, L, R, U2, D2>",
        Goal.eo_lr_ud: "<F, B, L2, R2, U2, D2>",
        Goal.eo_floppy_fb: "<L2, R2, U2, D2>",
        Goal.eo_floppy_lr: "<F2, B2, U2, D2>",
        Goal.eo_floppy_ud: "<F2, B2, L2, R2>",
        Goal.eo_htr: "<F2, B2, L2, R2, U2, D2>",
    }
    for goal, generator in edge_orientation_tags.items():
        patterns[goal] = Pattern.from_settings(
            name=goal.value,
            pieces=[Piece.edge],
            piece_orientations=MoveGenerator.from_str(generator),
            cube_size=cube_size,
        )

    # Non-symmetric center orientations
    center_orientation_tags = {
        Goal.xo_fb: ["z"],
        Goal.xo_lr: ["x"],
        Goal.xo_ud: ["y"],
    }
    for goal, sequence in center_orientation_tags.items():
        patterns[goal] = Pattern.from_settings(
            name=goal.value,
            solved_sequence=MoveSequence(sequence),
            keep=False,
            cube_size=cube_size,
        )

    # Non-symmetric corner orientations
    corner_orientation_tags = {
        Goal.co_fb: "<F, B, L2, R2, U2, D2>",
        Goal.co_lr: "<F2, B2, L, R, U2, D2>",
        Goal.co_ud: "<F2, B2, L2, R2, U, D>",
        Goal.co_htr: "<F2, B2, L2, R2, U2, D2>",
    }
    for goal, generator in corner_orientation_tags.items():
        patterns[goal] = Pattern.from_settings(
            name=goal.value,
            pieces=[Piece.corner],
            piece_orientations=MoveGenerator.from_str(generator),
            cube_size=cube_size,
        )

    # Non-symmetric corner and edge orientations

    # Composite patterns
    patterns[Goal.xo_htr] = patterns[Goal.xo_ud] & patterns[Goal.xo_lr] & patterns[Goal.xo_fb]
    patterns[Goal.eo] = patterns[Goal.eo_fb] | patterns[Goal.eo_lr] | patterns[Goal.eo_ud]
    patterns[Goal.co] = patterns[Goal.co_fb] | patterns[Goal.co_lr] | patterns[Goal.co_ud]
    patterns[Goal.dr_ud] = patterns[Goal.co_ud] & patterns[Goal.eo_fb_lr] & patterns[Goal.xo_htr]
    patterns[Goal.dr_fb] = patterns[Goal.co_fb] & patterns[Goal.eo_lr_ud] & patterns[Goal.xo_htr]
    patterns[Goal.dr_lr] = patterns[Goal.co_lr] & patterns[Goal.eo_fb_ud] & patterns[Goal.xo_htr]
    patterns[Goal.dr] = patterns[Goal.dr_ud] | patterns[Goal.dr_fb] | patterns[Goal.dr_lr]
    patterns[Goal.xx_cross] = patterns[Goal.xx_cross_adjacent] | patterns[Goal.xx_cross_diagonal]
    patterns[Goal.minus_slice] = (
        patterns[Goal.minus_slice_m] | patterns[Goal.minus_slice_s] | patterns[Goal.minus_slice_e]
    )
    patterns[Goal.leave_slice_m] = (
        patterns[Goal.minus_slice_m] & patterns[Goal.eo_ud] & patterns[Goal.xo_ud]
    )
    patterns[Goal.leave_slice_s] = (
        patterns[Goal.minus_slice_s] & patterns[Goal.eo_lr] & patterns[Goal.xo_lr]
    )
    patterns[Goal.leave_slice_e] = (
        patterns[Goal.minus_slice_e] & patterns[Goal.eo_fb] & patterns[Goal.xo_fb]
    )
    patterns[Goal.leave_slice] = (
        patterns[Goal.leave_slice_m] | patterns[Goal.leave_slice_s] | patterns[Goal.leave_slice_e]
    )
    patterns[Goal.htr_like] = patterns[Goal.co_htr] & patterns[Goal.eo_htr] & patterns[Goal.xo_htr]

    for goal in [goal for goal in patterns if not patterns[goal].keep]:
        del patterns[goal]
    LOGGER.debug(f"Created patterns in {timeit.default_timer() - t:.3f} seconds.")

    def entropy(goal: Goal) -> float:
        return patterns[goal].entropy

    t = timeit.default_timer()
    patterns = {goal: patterns[goal] for goal in sorted(patterns, key=entropy)}
    LOGGER.debug(f"Sorted patterns in {timeit.default_timer() - t:.3f} seconds.")

    return patterns
