from __future__ import annotations

from functools import lru_cache
import numpy as np

from rubiks_cube.permutation import SOLVED_STATE
from rubiks_cube.permutation import get_permutation
from rubiks_cube.permutation import get_generator_orientation
from rubiks_cube.permutation import create_mask
from rubiks_cube.permutation import generate_mask_symmetries
from rubiks_cube.tag.enumerations import Basic
from rubiks_cube.tag.enumerations import CFOP
from rubiks_cube.tag.enumerations import FewestMoves
from rubiks_cube.tag.enumerations import Progress
from rubiks_cube.utils.enumerations import Piece
from rubiks_cube.utils.sequence import Sequence


class CubexPattern:
    """
    Regular Cube Expression. Represents a matchable pattern.
    It consists of the following:
    - mask: A boolean mask that represents the fixed pieces to check.
    - orientations: A list of boolean masks that represent the relative pieces.
    """

    def __init__(
            self,
            mask: np.ndarray | None = None,
            orientations: list[np.ndarray] | None = None,
    ) -> None:
        self.mask = mask if mask is not None else np.zeros_like(SOLVED_STATE, dtype=bool)  # noqa E501
        self.orientations = orientations if orientations is not None else []

    def __repr__(self) -> str:
        return (
            f"CubexPattern(mask={self.mask}, orientations={self.orientations})"
        )

    def match(self, permutation: np.ndarray, goal: np.ndarray) -> bool:
        """
        Check if the permutation matches the pattern.
        """
        return np.array_equal(
            permutation[self.mask], goal[self.mask]
        ) and all(
            np.all(
                np.isin(permutation[orientation], goal[orientation])
            )
            for orientation in self.orientations
        )

    def __and__(self, other: CubexPattern) -> CubexPattern:
        """
        Combine two cube expressions with the AND operation.
        This will match the union of the two patterns.
        """
        return CubexPattern(
            mask=self.mask | other.mask,
            orientations=self.orientations + other.orientations,
        )

    def __rand__(self, other: CubexPattern) -> CubexPattern:
        return self & other

    def __eq__(self, other: CubexPattern) -> bool:
        return hash(self) == hash(other)

    def __hash__(self) -> int:
        return hash(
            (
                self.mask.tobytes(),
                tuple(
                    orientation.tobytes()
                    for orientation in self.orientations
                ),
            )
        )

    def create_symmetries(self) -> list[CubexPattern]:
        """Create all symmetries that matches the pattern."""
        if len(self.orientations) == 0:
            return [
                CubexPattern(mask=symmetries[0])
                for symmetries in generate_mask_symmetries(
                    masks=[self.mask]
                )
            ]
        # elif not np.any(self.mask):
        #     return [self]
        else:
            return [
                CubexPattern(mask=symmetries[0], orientations=symmetries[1:])
                for symmetries in generate_mask_symmetries(
                    masks=[self.mask] + self.orientations
                )
            ]


class Cubex:
    """
    Composite Cube Patterns. Represents a combination of patterns.
    TODO: Add way to check if a pattern is a subset of another pattern
    """

    def __init__(
        self,
        patterns: list[CubexPattern] | None = None,
        goal: np.ndarray | None = None,
    ) -> None:
        self.patterns = list(set(patterns)) if patterns is not None else [CubexPattern()]  # noqa E501
        self.goal = goal if goal is not None else SOLVED_STATE

    def __repr__(self) -> str:
        return f"Cubex(patterns={self.patterns}, goal={self.goal})"

    def __or__(self, other: Cubex) -> Cubex:
        """
        Combine two cube expressions with an OR operation.
        """
        return Cubex([*self.patterns, *other.patterns])

    def __ror__(self, other: Cubex) -> Cubex:
        return self | other

    def __and__(self, other: Cubex) -> Cubex:
        """
        Combine two cube expressions with an AND operation.
        Uses the cartesian product of the two sets.
        """
        return Cubex(
            [
                pattern & other_pattern
                for pattern in self.patterns
                for other_pattern in other.patterns
            ]
        )

    def __rand__(self, other: Cubex) -> Cubex:
        return self & other

    def __eq__(self, other: Cubex) -> bool:
        return self.patterns == other.patterns

    def __len__(self) -> int:
        return len(self.patterns)

    def match(self, input: Sequence | np.ndarray) -> bool:
        """
        Check if the permutation matches any of the patterns.
        """
        if isinstance(input, Sequence):
            input = get_permutation(sequence=input, ignore_rotations=True)
        return any(
            pattern.match(input, self.goal) for pattern in self.patterns
        )

    @classmethod
    def from_sequence(
        cls,
        scramble: Sequence,
    ) -> Cubex:
        """
        Create a cube expression from a scramble as goal.
        """
        return cls(
            patterns=[
                CubexPattern(mask=np.ones_like(SOLVED_STATE, dtype=bool))
            ],
            goal=get_permutation(
                sequence=scramble,
                ignore_rotations=False,
            ),
        )

    @classmethod
    def from_solved_after_sequence(
        cls,
        sequence: Sequence = Sequence(),
        invert: bool = False,
        ignore_rotations: bool = False,
    ) -> Cubex:
        """
        Create a cube expression from a sequence.
        """
        mask = create_mask(
            sequence=sequence,
            invert=invert,
            ignore_rotations=ignore_rotations,
        )
        return cls([CubexPattern(mask=mask)])

    @classmethod
    def from_generator_orientation(
        cls,
        pieces: list[Piece],
        generator: Sequence,
    ) -> Cubex:
        """
        Create a cube expression from a sequence.
        """
        orientations = []

        for piece in pieces:
            orientations.extend(
                get_generator_orientation(
                    piece=piece,
                    generator=generator,
                    ignore_rotations=False,
                )
            )

        if orientations:
            return cls(patterns=[CubexPattern(orientations=orientations)])
        return cls()

    def create_symmetries(self) -> None:
        """
        Create symmetries for the cube expression only if it has a mask.
        """
        new_patterns = []
        for pattern in self.patterns:
            new_patterns.extend(pattern.create_symmetries())
        self.patterns = new_patterns

    def optimize(self) -> None:
        """
        Optimize the cube expression.
        TODO: Remove idx from a orientation if in the mask
        TODO: Remove duplicate orientations that are equal,
          i.e. orientations A = orientations B if there is a bijection between
          the orientations of A and B.
        TODO: Prune orientation maps to be non-overlapping.
          The intersection of the orientations of A and B is orientated with
          respect to the mask of A and B, and thus is a new orientation.
          The part of A not in B is a new orientation, and the part of B not
          in A is a new orientation.
        TODO: After splitting the orientations into non-overlapping parts,
          remove the orientations that are equivalent each other, i.e. the
          orientations that are a bijection between each other.
        TODO: Make the orientation maps into lists of indices.
        """
        pass


@lru_cache(maxsize=1)
def get_cubex() -> dict[str, Cubex]:
    """
    Return a dictionary of cube expressions from the tag.
    """
    cubex_dict = {}

    # Symmetric masks
    mask_tags = {
        Basic.cp_layer.value: "M' S Dw",
        Basic.ep_layer.value: "M2 D2 F2 B2 Dw",
        Basic.layer.value: "Dw",
        CFOP.cross.value: "R L U2 R2 L2 U2 R L U",
        CFOP.f2l.value: "U",
        CFOP.x_cross.value: "R L' U2 R2 L U2 R U",
        CFOP.xx_cross_adjacent.value: "R L' U2 R' L U",
        CFOP.xx_cross_diagonal.value: "R' L' U2 R L U",
        CFOP.xxx_cross.value: "R U R' U",
        FewestMoves.block_1x2x2.value: "U R Fw",
        FewestMoves.block_1x2x3.value: "U Rw",
        FewestMoves.block_2x2x2.value: "U R F",
        FewestMoves.block_2x2x3.value: "U R",
        FewestMoves.block_2x3x3.value: "U",
        FewestMoves.solved_corners.value: "M' S E",
        FewestMoves.solved_edges.value: "E2 R L S2 L R' S2 R2 S M S M'",
        Progress.solved.value: "",
    }
    for tag, string in mask_tags.items():
        cubex_dict[tag] = Cubex.from_solved_after_sequence(
            sequence=Sequence(string)
        )

    # Symmetric corner orientations
    symmetric_corner_orientation_tags = {
        Basic.co_face.value: "U",
    }
    for tag, string in symmetric_corner_orientation_tags.items():
        cubex_dict[tag] = Cubex.from_generator_orientation(
            pieces=[Piece.corner],
            generator=Sequence(string),
        )

    # Symmetric edge orientations
    symmetric_edge_orientation_tags = {
        Basic.eo_face.value: "U",
    }
    for tag, string in symmetric_edge_orientation_tags.items():
        cubex_dict[tag] = Cubex.from_generator_orientation(
            pieces=[Piece.edge],
            generator=Sequence(string),
        )

    # Symmetric corner and edge orientations
    symmetric_edge_corner_orientation_tags = {
        Basic.face.value: "U",
    }
    for tag, string in symmetric_edge_corner_orientation_tags.items():
        cubex_dict[tag] = Cubex.from_generator_orientation(
            pieces=[Piece.corner, Piece.edge],
            generator=Sequence(string),
        )

    # Symmetric composite
    cubex_dict[CFOP.oll.value] = (
        cubex_dict[Basic.face.value] & cubex_dict[CFOP.f2l.value]
    )
    cubex_dict[CFOP.f2l_co.value] = (
        cubex_dict[Basic.co_face.value] & cubex_dict[CFOP.f2l.value]
    )
    cubex_dict[CFOP.f2l_eo.value] = (
        cubex_dict[Basic.eo_face.value] & cubex_dict[CFOP.f2l.value]
    )
    cubex_dict[CFOP.f2l_cp.value] = (
        cubex_dict[Basic.cp_layer.value] & cubex_dict[CFOP.f2l.value]
    )
    cubex_dict[CFOP.f2l_ep.value] = (
        cubex_dict[Basic.ep_layer.value] & cubex_dict[CFOP.f2l.value]
    )

    # Create symmetries for all cubexes defined above
    for cubex in cubex_dict.values():
        cubex.create_symmetries()

    # Non-symmetric masks
    mask_tags = {
        FewestMoves.minus_slice_m.value: "M",
        FewestMoves.minus_slice_s.value: "S",
        FewestMoves.minus_slice_e.value: "E",
    }
    for tag, string in mask_tags.items():
        cubex_dict[tag] = Cubex.from_solved_after_sequence(
            sequence=Sequence(string)
        )

    # Non-symmetric edge orientations
    edge_orientation_tags = {
        FewestMoves.eo_fb.value: "F2 B2 L R U D",
        FewestMoves.eo_lr.value: "F B L2 R2 U D",
        FewestMoves.eo_ud.value: "F B L R U2 D2",
        FewestMoves.eo_htr.value: "F2 B2 L2 R2 U2 D2",
    }
    for tag, string in edge_orientation_tags.items():
        cubex_dict[tag] = Cubex.from_generator_orientation(
            pieces=[Piece.edge],
            generator=Sequence(string),
        )

    # Non-symmetric corner orientations
    corner_orientation_tags = {
        FewestMoves.co_fb.value: "F B L2 R2 U2 D2",
        FewestMoves.co_lr.value: "F2 B2 L R U2 D2",
        FewestMoves.co_ud.value: "F2 B2 L2 R2 U D",
        FewestMoves.co_htr.value: "F2 B2 L2 R2 U2 D2",
    }
    for tag, string in corner_orientation_tags.items():
        cubex_dict[tag] = Cubex.from_generator_orientation(
            pieces=[Piece.corner],
            generator=Sequence(string),
        )

    # Non-symmetric corner and edge orientations

    # Composite patterns
    cubex_dict[FewestMoves.eo.value] = (
        cubex_dict[FewestMoves.eo_fb.value]
        | cubex_dict[FewestMoves.eo_lr.value]
        | cubex_dict[FewestMoves.eo_ud.value]
    )
    cubex_dict[FewestMoves.co.value] = (
        cubex_dict[FewestMoves.co_fb.value]
        | cubex_dict[FewestMoves.co_lr.value]
        | cubex_dict[FewestMoves.co_ud.value]
    )
    cubex_dict[FewestMoves.dr_ud.value] = (
        cubex_dict[FewestMoves.co_ud.value]
        & cubex_dict[FewestMoves.eo_fb.value]
        & cubex_dict[FewestMoves.eo_lr.value]
    )
    cubex_dict[FewestMoves.dr_fb.value] = (
        cubex_dict[FewestMoves.co_fb.value]
        & cubex_dict[FewestMoves.eo_lr.value]
        & cubex_dict[FewestMoves.eo_ud.value]
    )
    cubex_dict[FewestMoves.dr_lr.value] = (
        cubex_dict[FewestMoves.co_lr.value]
        & cubex_dict[FewestMoves.eo_fb.value]
        & cubex_dict[FewestMoves.eo_ud.value]
    )
    cubex_dict[FewestMoves.dr.value] = (
        cubex_dict[FewestMoves.dr_ud.value]
        | cubex_dict[FewestMoves.dr_fb.value]
        | cubex_dict[FewestMoves.dr_lr.value]
    )
    cubex_dict[CFOP.xx_cross.value] = (
        cubex_dict[CFOP.xx_cross_adjacent.value]
        | cubex_dict[CFOP.xx_cross_diagonal.value]
    )
    cubex_dict[FewestMoves.minus_slice.value] = (
        cubex_dict[FewestMoves.minus_slice_m.value]
        | cubex_dict[FewestMoves.minus_slice_s.value]
        | cubex_dict[FewestMoves.minus_slice_e.value]
    )
    cubex_dict[FewestMoves.leave_slice_m.value] = (
        cubex_dict[FewestMoves.minus_slice_m.value]
        & cubex_dict[FewestMoves.eo_lr.value]
    )
    cubex_dict[FewestMoves.leave_slice_s.value] = (
        cubex_dict[FewestMoves.minus_slice_s.value]
        & cubex_dict[FewestMoves.eo_lr.value]
    )
    cubex_dict[FewestMoves.leave_slice_e.value] = (
        cubex_dict[FewestMoves.minus_slice_e.value]
        & cubex_dict[FewestMoves.eo_ud.value]
    )
    cubex_dict[FewestMoves.leave_slice.value] = (
        cubex_dict[FewestMoves.leave_slice_m.value]
        | cubex_dict[FewestMoves.leave_slice_s.value]
        | cubex_dict[FewestMoves.leave_slice_e.value]
    )
    cubex_dict[FewestMoves.htr_like.value] = (
        cubex_dict[FewestMoves.co_htr.value]
        & cubex_dict[FewestMoves.eo_htr.value]
    )

    #    OPTIMIZE    #
    for cubex in cubex_dict.values():
        cubex.optimize()

    return cubex_dict


def main() -> None:
    cbxs = get_cubex()
    sequence = Sequence("R' F R' B2 R F' R'")

    print(f'\nSequence "{sequence}" tagged with {len(cbxs)} tags:\n')
    for tag, cbx in sorted(cbxs.items()):
        print(f"{tag} ({len(cbx)}):", cbx.match(sequence))
    print()


if __name__ == "__main__":
    main()
