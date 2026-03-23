from __future__ import annotations

import logging
import timeit
from functools import lru_cache
from math import log2
from threading import Lock
from typing import TYPE_CHECKING
from typing import Any
from typing import Self
from typing import Sequence

import attrs
import numpy as np

from rubiks_cube.autotagger.subset import distinguish_htr
from rubiks_cube.configuration.enumeration import Goal
from rubiks_cube.configuration.enumeration import Piece
from rubiks_cube.configuration.enumeration import Variant
from rubiks_cube.move.generator import MoveGenerator
from rubiks_cube.move.meta import MoveMeta
from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.representation.mask import get_fixed_mask
from rubiks_cube.representation.mask import get_pieces_mask
from rubiks_cube.representation.pattern import generate_pattern_variants
from rubiks_cube.representation.pattern import get_empty_pattern
from rubiks_cube.representation.pattern import get_identity_pattern
from rubiks_cube.representation.pattern import merge_patterns
from rubiks_cube.representation.pattern import pattern_combinations
from rubiks_cube.representation.pattern import pattern_from_generator
from rubiks_cube.representation.pattern import pattern_implies

if TYPE_CHECKING:
    from rubiks_cube.configuration.types import CubePattern
    from rubiks_cube.configuration.types import CubePermutation
    from rubiks_cube.configuration.types import PermutationValidator


LOGGER = logging.getLogger(__name__)
GET_PATTERNS_LOCK = Lock()


@attrs.mutable
class Pattern:
    variants: dict[Variant, CubePattern]
    validator: PermutationValidator | None = None

    @classmethod
    def from_settings(
        cls,
        move_meta: MoveMeta,
        variant: Variant,
        fixed_sequence: MoveSequence | None,
        pieces: list[Piece] | None = None,
        orientation_generator: MoveGenerator | None = None,
    ) -> Self:
        """Create Pattern from a variant, a fixed sequence and optional orientations.

        Args:
            move_meta (MoveMeta): Meta information about moves.
            variant (Variant): Initial variant to create other variants from.
            fixed_sequence (MoveSequence | None): Sequence for indices that remain fixed.
            pieces (list[Piece] | None, optional): List of pieces.
            orientation_generator (MoveGenerator, optional): Generators conserving orientations.

        Returns:
            Self: Patterns.
        """
        if fixed_sequence is None:
            fixed_pattern = get_empty_pattern(cube_size=move_meta.cube_size)
        else:
            fixed_mask = get_fixed_mask(sequence=fixed_sequence, move_meta=move_meta)
            fixed_pattern = get_identity_pattern(size=move_meta.size)
            fixed_pattern[~fixed_mask] = 0

        # Find the orientations of the pieces given the generator
        if pieces is not None and orientation_generator is not None:
            mask = get_pieces_mask(pieces=pieces, move_meta=move_meta)
            orientations_pattern = pattern_from_generator(
                generator=orientation_generator,
                mask=mask,
                move_meta=move_meta,
            )
            # Don't keep elements that appear only once
            unique, counts = np.unique(orientations_pattern, return_counts=True)
            mask = np.isin(orientations_pattern, unique[counts == 1])
            orientations_pattern[mask] = 0
        else:
            orientations_pattern = get_empty_pattern(cube_size=move_meta.cube_size)

        # Store all variants
        variants = {variant: merge_patterns((fixed_pattern, orientations_pattern))}

        # Create new variants from the initial variant
        if variant is not Variant.none:
            initial_variant, initial_pattern = next(iter(variants.items()))
            variants = generate_pattern_variants(
                pattern=initial_pattern,
                initial_variant=initial_variant,
                move_meta=move_meta,
            )
        return cls(variants=variants)

    @classmethod
    def from_merge(
        cls,
        move_meta: MoveMeta,
        variant: Variant,
        patterns: Sequence[CubePattern],
    ) -> Self:
        variants = {variant: merge_patterns(patterns=patterns)}
        if variant is not Variant.none:
            initial_variant, initial_pattern = next(iter(variants.items()))
            variants = generate_pattern_variants(
                pattern=initial_pattern,
                initial_variant=initial_variant,
                move_meta=move_meta,
            )
        return cls(variants=variants)

    def __and__(self, other: Pattern) -> Pattern:
        return Pattern(
            variants={
                variant: merge_patterns((pattern, other_pattern))
                for variant, pattern in self.variants.items()
                for _other_variant, other_pattern in other.variants.items()
            },
        )

    def __getitem__(self, key: Variant) -> CubePattern:
        return self.variants[key]

    def __contains__(self, other: Any) -> bool:
        if isinstance(other, Pattern):
            return any(
                pattern_implies(variant, other_variant)
                for variant in self.variants.values()
                for other_variant in other.variants.values()
            )
        return False

    def __len__(self) -> int:
        return len(self.variants)

    def match(self, permutation: CubePermutation) -> Variant | None:
        for variant, pattern in self.variants.items():
            if np.array_equal(pattern[permutation], pattern):
                if self.validator is not None and not self.validator(permutation):
                    return None
                return variant
        return None

    def calc_combinations(self, move_meta: MoveMeta) -> int:
        """Sum of the number of combinations for each pattern."""
        initial_pattern = next(iter(self.variants.values()))
        n = len(self) * pattern_combinations(initial_pattern, move_meta)

        # TODO: Fix hack for counting with validator. Right now, only htr has a validator
        if self.validator is not None:
            return n // 6
        return n

    def entropy(self, move_meta: MoveMeta) -> float:
        """Find the estimated entropy of the patterns."""
        return log2(self.calc_combinations(move_meta=move_meta))


# TODO: Implement
def get_2x2_patterns(move_meta: MoveMeta) -> dict[Goal, Pattern]:
    patterns: dict[Goal, Pattern] = {}
    return patterns


def get_3x3_patterns(move_meta: MoveMeta) -> dict[Goal, Pattern]:
    patterns: dict[Goal, Pattern] = {}

    # Fixed goals
    fixed_goals: dict[tuple[Goal, Variant], list[str]] = {
        (Goal.none, Variant.none): ["x", "y"],
        (Goal.cp_layer, Variant.up): ["M'", "S", "Dw"],
        (Goal.ep_layer, Variant.up): ["M2", "D2", "F2", "B2", "Dw"],
        (Goal.layer, Variant.up): ["Dw"],
        (Goal.cross, Variant.down): ["R", "L", "U2", "R2", "L2", "U2", "R", "L", "U"],
        (Goal.f2l, Variant.down): ["U"],
        (Goal.x_cross, Variant.down_bl): ["R", "L'", "U2", "R2", "L", "U2", "R", "U"],
        (Goal.xx_cross_adjacent, Variant.down_b): ["R", "L'", "U2", "R'", "L", "U"],
        (Goal.xx_cross_diagonal, Variant.down_bl_fr): ["R'", "L'", "U2", "R", "L", "U"],
        (Goal.xxx_cross, Variant.down_fr): ["R", "U", "R'", "U"],
        (Goal.block_1x1x3, Variant.bl): ["Fw", "Rw"],
        (Goal.block_1x2x2, Variant.back_dl): ["U", "R", "Fw"],
        (Goal.block_1x2x3, Variant.dl): ["U", "Rw"],
        (Goal.block_2x2x2, Variant.down_bl): ["U", "R", "F"],
        (Goal.block_2x2x3, Variant.dl): ["U", "R"],
        (Goal.corners, Variant.none): ["M'", "S", "E"],
        (Goal.edges, Variant.none): [
            "E2",
            "R",
            "L",
            "S2",
            "L",
            "R'",
            "S2",
            "R2",
            "S",
            "M",
            "S",
            "M'",
        ],
        (Goal.solved, Variant.none): [],
        (Goal.minus_slice, Variant.ud): ["E"],
    }
    for (goal, variant), moves in fixed_goals.items():
        patterns[goal] = Pattern.from_settings(
            move_meta=move_meta,
            variant=variant,
            fixed_sequence=MoveSequence(moves),
        )

    # Orientations
    patterns[Goal.co_face] = Pattern.from_settings(
        move_meta=move_meta,
        variant=Variant.up,
        fixed_sequence=MoveSequence(["y"]),
        pieces=[Piece.corner],
        orientation_generator=MoveGenerator.from_str("<U>"),
    )
    patterns[Goal.eo_face] = Pattern.from_settings(
        move_meta=move_meta,
        fixed_sequence=MoveSequence(["y"]),
        pieces=[Piece.edge],
        orientation_generator=MoveGenerator.from_str("<U>"),
        variant=Variant.up,
    )
    patterns[Goal.face] = Pattern.from_settings(
        move_meta=move_meta,
        variant=Variant.up,
        fixed_sequence=MoveSequence(["y"]),
        pieces=[Piece.corner, Piece.edge],
        orientation_generator=MoveGenerator.from_str("<U>"),
    )

    # Symmetric edge orientations
    edge_orientation_symmetric: dict[tuple[Goal, Variant], str] = {
        (Goal.eo, Variant.fb): "<F2, B2, L, R, U, D>",
        (Goal.eo_floppy, Variant.fb): "<L2, R2, U2, D2>",
    }
    for (goal, variant), generator_str in edge_orientation_symmetric.items():
        patterns[goal] = Pattern.from_settings(
            move_meta=move_meta,
            variant=variant,
            fixed_sequence=None,
            pieces=[Piece.edge],
            orientation_generator=MoveGenerator.from_str(generator_str),
        )

    # Symmetric corner orientations
    corner_orientation_symmetric: dict[tuple[Goal, Variant], str] = {
        (Goal.co, Variant.fb): "<F, B, L2, R2, U2, D2>",
    }
    for (goal, variant), generator_str in corner_orientation_symmetric.items():
        patterns[goal] = Pattern.from_settings(
            move_meta=move_meta,
            variant=variant,
            fixed_sequence=None,
            pieces=[Piece.corner],
            orientation_generator=MoveGenerator.from_str(generator_str),
        )

    # Symmetric center orientations
    patterns[Goal.xo] = Pattern.from_settings(
        move_meta=move_meta,
        variant=Variant.fb,
        fixed_sequence=None,
        pieces=[Piece.center],
        orientation_generator=MoveGenerator.from_str("<x2, z>"),
    )

    # TODO: Floppy reduction does not fuse edges and corners together
    # Symmetric edge + corner orientations
    edge_orientation_symmetric: dict[tuple[Goal, Variant], str] = {
        (Goal.floppy, Variant.fb): "<L2, R2, U2, D2>",
    }
    for (goal, variant), generator_str in edge_orientation_symmetric.items():
        patterns[goal] = Pattern.from_settings(
            move_meta=move_meta,
            variant=variant,
            fixed_sequence=None,
            pieces=[Piece.edge, Piece.corner],
            orientation_generator=MoveGenerator.from_str(generator_str),
        )

    # Symmetric composite
    patterns[Goal.f2l_face] = patterns[Goal.face] & patterns[Goal.f2l]
    patterns[Goal.f2l_co] = patterns[Goal.co_face] & patterns[Goal.f2l]
    patterns[Goal.f2l_eo] = patterns[Goal.eo_face] & patterns[Goal.f2l]
    patterns[Goal.f2l_cp] = patterns[Goal.cp_layer] & patterns[Goal.f2l]
    patterns[Goal.f2l_ep] = patterns[Goal.ep_layer] & patterns[Goal.f2l]
    patterns[Goal.f2l_ep_co] = patterns[Goal.f2l_co] & patterns[Goal.ep_layer]
    patterns[Goal.f2l_eo_cp] = patterns[Goal.f2l_cp] & patterns[Goal.eo_face]

    # Non-symmetric edge orientations
    edge_orientation_tags: dict[tuple[Goal, Variant], str] = {
        (Goal.eo_htr, Variant.none): "<F2, B2, L2, R2, U2, D2>",
    }
    for (goal, variant), generator_str in edge_orientation_tags.items():
        patterns[goal] = Pattern.from_settings(
            move_meta=move_meta,
            variant=variant,
            fixed_sequence=None,
            pieces=[Piece.edge],
            orientation_generator=MoveGenerator.from_str(generator_str),
        )

    # Non-symmetric corner orientations
    corner_orientation_tags: dict[tuple[Goal, Variant], str] = {
        (Goal.co_htr, Variant.none): "<F2, B2, L2, R2, U2, D2>",
    }
    for (goal, variant), generator_str in corner_orientation_tags.items():
        patterns[goal] = Pattern.from_settings(
            move_meta=move_meta,
            variant=variant,
            fixed_sequence=None,
            pieces=[Piece.corner],
            orientation_generator=MoveGenerator.from_str(generator_str),
        )

    # Composite patterns
    patterns[Goal.xo_htr] = Pattern.from_merge(
        move_meta=move_meta,
        variant=Variant.none,
        patterns=list(patterns[Goal.xo].variants.values()),
    )

    patterns[Goal.dr] = Pattern.from_merge(
        move_meta=move_meta,
        variant=Variant.ud,
        patterns=[
            patterns[Goal.co][Variant.ud],
            patterns[Goal.eo][Variant.fb],
            patterns[Goal.eo][Variant.lr],
            patterns[Goal.xo_htr][Variant.none],
        ],
    )

    patterns[Goal.leave_slice] = Pattern.from_merge(
        move_meta=move_meta,
        variant=Variant.ud,
        patterns=[
            patterns[Goal.minus_slice][Variant.ud],
            patterns[Goal.eo][Variant.fb],
            patterns[Goal.eo][Variant.lr],
            patterns[Goal.xo][Variant.fb],
            patterns[Goal.xo][Variant.lr],
        ],
    )

    patterns[Goal.htr_like] = patterns[Goal.co_htr] & patterns[Goal.eo_htr] & patterns[Goal.xo_htr]

    # Add real htr with permutation validator
    htr_like = patterns[Goal.htr_like]
    patterns[Goal.htr] = Pattern(
        variants=htr_like.variants,
        validator=lambda permutation: distinguish_htr(permutation) == "real",
    )

    # TODO: Consider doing composite patterns Goal.xx_cross (adj or diag)

    return patterns


# TODO: Implement
def get_4x4_patterns(move_meta: MoveMeta) -> dict[Goal, Pattern]:
    patterns: dict[Goal, Pattern] = {}
    return patterns


def sort_using_entropy(patterns: dict[Goal, Pattern], move_meta: MoveMeta) -> dict[Goal, Pattern]:
    """Sort the patterns using a proxy for the entropy.

    For future, consider an anytime iterative inclusion/exclusion sorting algorithm.
    """

    def entropy(goal: Goal) -> float:
        return patterns[goal].entropy(move_meta=move_meta)

    return {goal: patterns[goal] for goal in sorted(patterns, key=entropy)}


@lru_cache(maxsize=10)
def _get_cached_patterns(cube_size: int) -> dict[Goal, Pattern]:
    """Return a cached dictionary of patterns from goals given the cube size."""
    assert cube_size == 3

    move_meta = MoveMeta.from_cube_size(cube_size)

    t = timeit.default_timer()
    if move_meta.cube_size == 2:
        patterns = get_2x2_patterns(move_meta=move_meta)
    elif move_meta.cube_size == 3:
        patterns = get_3x3_patterns(move_meta=move_meta)
    elif move_meta.cube_size == 4:
        patterns = get_4x4_patterns(move_meta=move_meta)
    else:
        raise ValueError(f"Cube size is not supported. Expected 2, 3 or 4, got {cube_size}")

    LOGGER.debug(f"Created patterns in {timeit.default_timer() - t:.3f} seconds.")

    if cube_size < 4:
        t = timeit.default_timer()
        patterns = sort_using_entropy(patterns, move_meta=move_meta)
        LOGGER.debug(f"Sorted patterns in {timeit.default_timer() - t:.3f} seconds.")

    return patterns


def get_patterns(cube_size: int) -> dict[Goal, Pattern]:
    """Return a dictionary of patterns given the cube size.

    Args:
        cube_size (int): Size of the cube.

    Returns:
        dict[Goal, Pattern]: Dictionary of goals and their patterns.

    Note:
        - Caches patterns with single-flight initialization per process.
          `functools.lru_cache` can execute the wrapped function
          more than once when concurrent cold calls happen.
    """
    with GET_PATTERNS_LOCK:
        return _get_cached_patterns(cube_size)
