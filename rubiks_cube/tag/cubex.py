from __future__ import annotations

from functools import lru_cache
from math import log2
from typing import Any
from typing import Literal

import numpy as np

from rubiks_cube.configuration import CUBE_SIZE
from rubiks_cube.configuration.enumeration import Piece
from rubiks_cube.configuration.enumeration import Symmetry
from rubiks_cube.configuration.enumeration import Tag
from rubiks_cube.configuration.types import CubePattern
from rubiks_cube.configuration.types import CubePermutation
from rubiks_cube.move.generator import MoveGenerator
from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.state.mask import get_piece_mask
from rubiks_cube.state.mask import get_rubiks_cube_mask
from rubiks_cube.state.pattern import generate_pattern_symmetries
from rubiks_cube.state.pattern import generate_pattern_symmetries_from_subset
from rubiks_cube.state.pattern import get_empty_pattern
from rubiks_cube.state.pattern import get_solved_pattern
from rubiks_cube.state.pattern import merge_patterns
from rubiks_cube.state.pattern import pattern_combinations
from rubiks_cube.state.pattern import pattern_from_generator


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
        subset: Symmetry | None = None,
        combinations: int | None = None,
        keep: bool = True,
    ) -> None:
        self.patterns = patterns
        self.names = names
        self._keep = keep
        self._combinations = combinations
        self._symmetry = subset

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
            subset=self._symmetry or other._symmetry,
            keep=self._keep or other._keep,
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
    def combinations(self) -> int:
        """Find the number of combinations for each pattern."""
        if self._combinations is None:
            self._combinations = sum(
                pattern_combinations(pattern, cube_size=CUBE_SIZE) for pattern in self.patterns
            )
        return self._combinations

    @property
    def entropy(self) -> float:
        """Find the estimated entropy of the patterns.
        This is the number of bits required to identify the permutation,
        given that at least one of the patterns is matched.
        The entropy of a single pattern is

            H(pattern) = -sum_{x in X} P[x] * log2(P[x]),

        where X is the set of all permutations where the pattern holds, and P[x] is the
        probability of the permutation x. Assuming a uniform propability, the entropy reduces to

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
        subset: Symmetry | None = None,
        keep: bool = True,
        cube_size: int = CUBE_SIZE,
    ) -> Cubex:
        """Cube expression from pieces that are solved after applying a sequence of moves.

        Args:
            name (str): Name of the cube expression.
            solved_sequence (MoveSequence, optional): Sequence for solved pieces.
            pieces (list[Piece], optional): List of pieces.
            piece_orientations (MoveGenerator, optional): Find conserved orientations of the pieces.
            subset (Symmetry, optional): Name of the specific subset to create symmetries.
            keep (bool, optional): Wether to keep the pattern. Defaults to True.
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
            subset=subset,
            keep=keep,
        )

    def create_symmetries(self, cube_size: int = CUBE_SIZE) -> None:
        """Create symmetries for the cube expression."""
        if self._symmetry is None:
            return

        new_patterns = []
        new_names = []

        for pattern, name in zip(self.patterns, self.names):
            subset_patterns, subset_names = generate_pattern_symmetries_from_subset(
                pattern=pattern,
                symmetry=self._symmetry,
                prefix=self.names[0],
                cube_size=cube_size,
            )
            new_patterns.extend(subset_patterns)
            new_names.extend(subset_names)

        # Old way to generate symmetries
        use_old = False
        if use_old:
            for pattern, name in zip(self.patterns, self.names):
                symmetries = generate_pattern_symmetries(
                    pattern=pattern,
                    generator=MoveGenerator("<x, y>"),
                    cube_size=cube_size,
                )
                for i, symmetry in enumerate(symmetries):
                    new_patterns.append(symmetry)
                    if i == 0:
                        new_names.append(f"{name}-{self._symmetry.value}")
                    else:
                        new_names.append(f"{name}-{i}")

        # Update the patterns and names
        self.patterns = new_patterns
        self.names = new_names


@lru_cache(maxsize=1)
def get_cubexes(
    sort_strategy: Literal["entropy", "affected", "none"] = "entropy",
    cube_size: int = CUBE_SIZE,
) -> dict[str, Cubex]:
    """Return a dictionary of cube expressions for the cube size.

    Args:
        cube_size (int, optional): Size of the cube. Defaults to CUBE_SIZE.

    Returns:
        dict[str, Cubex]: Dictionary of cube expressions.
    """
    cubexes: dict[Tag, Cubex] = {}

    # Symmetric solved tags
    solved_tags = {
        Tag.cp_layer: ("M' S Dw", Symmetry.up),
        Tag.ep_layer: ("M2 D2 F2 B2 Dw", Symmetry.up),
        Tag.layer: ("Dw", Symmetry.up),
        Tag.cross: ("R L U2 R2 L2 U2 R L U", Symmetry.down),
        Tag.f2l: ("U", Symmetry.down),
        Tag.x_cross: ("R L' U2 R2 L U2 R U", Symmetry.down_bl),
        Tag.xx_cross_adjacent: ("R L' U2 R' L U", Symmetry.down_b),
        Tag.xx_cross_diagonal: ("R' L' U2 R L U", Symmetry.down),  # down bl+fr
        Tag.xxx_cross: ("R U R' U", Symmetry.down_fr),
        Tag.block_1x1x3: ("Fw Rw", Symmetry.bl),
        Tag.block_1x2x2: ("U R Fw", Symmetry.down_bl),
        Tag.block_1x2x3: ("U Rw", Symmetry.dl),
        Tag.block_2x2x2: ("U R F", Symmetry.down_bl),
        Tag.block_2x2x3: ("U R", Symmetry.dl),
        Tag.corners: ("M' S E", None),
        Tag.edges: ("E2 R L S2 L R' S2 R2 S M S M'", None),
        Tag.solved: ("", None),
    }
    for tag, (seq, subset) in solved_tags.items():
        cubexes[tag] = Cubex.from_settings(
            name=tag.value,
            solved_sequence=MoveSequence(seq),
            subset=subset,
            cube_size=cube_size,
        )

    # Symmetric orientations
    cubexes[Tag.co_face] = Cubex.from_settings(
        name=Tag.co_face.value,
        solved_sequence=MoveSequence("y"),
        pieces=[Piece.corner],
        piece_orientations=MoveGenerator("<U>"),
        subset=Symmetry.up,
        cube_size=cube_size,
    )
    cubexes[Tag.eo_face] = Cubex.from_settings(
        name=Tag.eo_face.value,
        solved_sequence=MoveSequence("y"),
        pieces=[Piece.edge],
        piece_orientations=MoveGenerator("<U>"),
        subset=Symmetry.up,
        cube_size=cube_size,
    )
    cubexes[Tag.face] = Cubex.from_settings(
        name=Tag.face.value,
        solved_sequence=MoveSequence("y"),
        pieces=[Piece.corner, Piece.edge],
        piece_orientations=MoveGenerator("<U>"),
        subset=Symmetry.up,
        cube_size=cube_size,
    )

    # Symmetric composite
    cubexes[Tag.f2l_face] = cubexes[Tag.f2l] & cubexes[Tag.face]
    cubexes[Tag.f2l_co] = cubexes[Tag.f2l] & cubexes[Tag.co_face]
    cubexes[Tag.f2l_eo] = cubexes[Tag.f2l] & cubexes[Tag.eo_face]
    cubexes[Tag.f2l_cp] = cubexes[Tag.f2l] & cubexes[Tag.cp_layer]
    cubexes[Tag.f2l_ep] = cubexes[Tag.f2l] & cubexes[Tag.ep_layer]
    cubexes[Tag.f2l_ep_co] = cubexes[Tag.f2l_co] & cubexes[Tag.ep_layer]
    cubexes[Tag.f2l_eo_cp] = cubexes[Tag.f2l_cp] & cubexes[Tag.eo_face]

    # Create symmetries for all cubexes defined above
    for tag, cubex in cubexes.items():
        cubex.create_symmetries(cube_size=cube_size)

    # Non-symmetric tags
    mask_tags = {
        Tag.minus_slice_m: "M",
        Tag.minus_slice_s: "S",
        Tag.minus_slice_e: "E",
    }
    for tag, string in mask_tags.items():
        cubexes[tag] = Cubex.from_settings(
            name=tag.value,
            solved_sequence=MoveSequence(string),
            cube_size=cube_size,
        )

    # Non-symmetric edge orientations
    edge_orientation_tags = {
        Tag.eo_fb: "<F2, B2, L, R, U, D>",
        Tag.eo_lr: "<F, B, L2, R2, U, D>",
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
            name=tag.value,
            pieces=[Piece.edge],
            piece_orientations=MoveGenerator(gen),
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
            name=tag.value,
            solved_sequence=MoveSequence(seq),
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
            name=tag.value,
            pieces=[Piece.corner],
            piece_orientations=MoveGenerator(gen),
            cube_size=cube_size,
        )

    # Non-symmetric corner and edge orientations

    # Composite patterns
    cubexes[Tag.eo] = cubexes[Tag.eo_fb] | cubexes[Tag.eo_lr] | cubexes[Tag.eo_ud]
    cubexes[Tag.co] = cubexes[Tag.co_fb] | cubexes[Tag.co_lr] | cubexes[Tag.co_ud]
    cubexes[Tag.xo_all] = cubexes[Tag.xo_ud] & cubexes[Tag.xo_fb]
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
    cubexes[Tag.htr_like] = cubexes[Tag.co_htr] & cubexes[Tag.eo_htr] & cubexes[Tag.xo_all]

    # Remove the cubexes that are not marked to keep
    to_delete = []
    for tag in cubexes:
        if not cubexes[tag]._keep:
            to_delete.append(tag)
    for tag in to_delete:
        del cubexes[tag]

    # Sort the cubexes by their entropy (equiv. to the number of combinations)
    if sort_strategy == "entropy":
        cubexes = {
            tag: cubexes[tag] for tag in sorted(cubexes, key=lambda tag: cubexes[tag].entropy)
        }
    elif sort_strategy == "affected":
        cubexes = {
            tag: cubexes[tag]
            for tag in sorted(
                cubexes,
                key=lambda tag: cubexes[tag].combinations,
                reverse=True,
            )
        }

    return {tag.value: collection for tag, collection in cubexes.items()}
