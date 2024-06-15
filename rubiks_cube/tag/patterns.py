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


class CubePattern:
    """
    Regular Cube Expression. Represents a matchable pattern.
    It consists of the following:
    - mask: A boolean mask that represents the fixed pieces to check.
    - orientations: A list of boolean masks that represent the relative pieces.
    """

    def __init__(
            self,
            mask: np.ndarray | None = None,
            relative_masks: list[np.ndarray] | None = None,
            orientations: list[np.ndarray] | None = None,
    ) -> None:
        self.mask = mask if mask is not None else np.zeros_like(SOLVED_STATE, dtype=bool)  # noqa E501
        self.relative_masks = relative_masks if relative_masks is not None else []  # noqa E501
        self.orientations = orientations if orientations is not None else []
        assert len(self.mask) == len(SOLVED_STATE)

    def __repr__(self) -> str:
        if np.sum(self.mask) == 0:
            mask_repr = "None"
        else:
            mask_repr = self.mask
        return (
            f"CubePattern(mask={mask_repr}, \
                orientations={self.orientations}), \
                relative_masks={self.relative_masks}"
        )

    def _match_mask(self, permutation: np.ndarray, goal: np.ndarray) -> bool:
        return np.array_equal(permutation[self.mask], goal[self.mask])

    def _match_orientations(self, permutation: np.ndarray, goal: np.ndarray) -> bool:  # noqa E501
        return all(
            np.all(np.isin(permutation[orientation], goal[orientation]))
            for orientation in self.orientations
        )

    def _match_relative_masks(self, permutation: np.ndarray, goal: np.ndarray) -> bool:  # noqa E501
        # Precompute sets of masked parts for permutation and goal
        perm_sets = [
            set(permutation[relative_mask])
            for relative_mask in self.relative_masks
        ]
        goal_sets = [
            set(goal[relative_mask_in])
            for relative_mask_in in self.relative_masks
        ]

        # Compare the sets
        return all(
            any(perm_set == goal_set for goal_set in goal_sets)
            for perm_set in perm_sets
        )

    def match(self, permutation: np.ndarray, goal: np.ndarray) -> bool:
        """
        Check if the permutation matches the pattern.
        """
        return (
            self._match_mask(permutation, goal)
            and self._match_orientations(permutation, goal)
            and self._match_relative_masks(permutation, goal)
        )

    def __and__(self, other: CubePattern) -> CubePattern:
        """
        Combine two cube expressions with the AND operation.
        This will match the union of the two patterns.
        """
        return CubePattern(
            mask=self.mask | other.mask,
            orientations=self.orientations + other.orientations,
            relative_masks=self.relative_masks + other.relative_masks,
        )

    def __rand__(self, other: CubePattern) -> CubePattern:
        return self & other

    def __eq__(self, other: CubePattern) -> bool:
        return hash(self) == hash(other)

    def __hash__(self) -> int:
        return hash(
            (
                self.mask.tobytes(),
                tuple(
                    orientation.tobytes()
                    for orientation in self.orientations
                ),
                tuple(
                    relative_mask.tobytes()
                    for relative_mask in self.relative_masks
                ),
            )
        )

    def create_symmetries(self) -> list[CubePattern]:
        """Create all symmetries that matches the pattern."""
        n_orientations = len(self.orientations)
        return [
            CubePattern(
                mask=symmetries[0],
                orientations=symmetries[1:n_orientations + 1],
                relative_masks=symmetries[n_orientations + 1:]
            )
            for symmetries in generate_mask_symmetries(
                masks=[self.mask] + self.orientations + self.relative_masks
            )
        ]


class Cubex:
    """
    Composite Cube Patterns. Represents a combination of patterns.
    """

    def __init__(
        self,
        patterns: list[CubePattern] | None = None,
        goal: np.ndarray | None = None,
    ) -> None:
        self.patterns = list(set(patterns)) if patterns is not None else [CubePattern()]  # noqa E501
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
            permutation = get_permutation(sequence=input, orientate_after=True)
        else:
            permutation = input
        return any(
            pattern.match(permutation, self.goal) for pattern in self.patterns
        )

    @classmethod
    def from_solved_after_sequence(
        cls,
        sequence: Sequence = Sequence(),
        invert: bool = False,
        orientate_after: bool = False,
        kind: str = "permutation",
    ) -> Cubex:
        """
        Create a cube expression from the pieces that are solved after
        applying a sequence of moves.
        """
        mask = create_mask(
            sequence=sequence,
            invert=invert,
            orientate_after=orientate_after,
        )
        if kind == "orientation":
            return cls([CubePattern(orientations=[mask])])
        elif kind == "permutation":
            return cls([CubePattern(mask=mask)])
        else:
            raise ValueError(f"Unknown kind: {kind}")

    @classmethod
    def from_generator_orientation(
        cls,
        pieces: list[Piece],
        generator: str,
    ) -> Cubex:
        """
        Create a cube expression from a the orientation that is perserved
        in the generator. Generator is a sequence of moves that "generates" the
        orientation.
        """
        orientations = []

        for piece in pieces:
            orientations.extend(
                get_generator_orientation(
                    piece=piece,
                    generator=generator,
                    orientate_after=False,
                )
            )

        if orientations:
            return cls(patterns=[CubePattern(orientations=orientations)])
        return cls()

    @classmethod
    def from_relativly_solved(
        cls,
        sequence: str,
        generator: str,
    ) -> Cubex:
        """
        Create a cube expression from a sequence. The pieces affected by the
        sequence are considered solved. Then it will automatically find the
        pieces that are affected in the same way, i.e. the location relative to
        the other piece is the same.
        """
        assert generator[0] == "<" and generator[-1] == ">", (
            "Generator must be enclosed in '<' and '>'."
        )
        mask = create_mask(
            sequence=sequence,
            invert=False,
            orientate_after=False,
        )
        group_of_relative_masks = generate_mask_symmetries(
            masks=[mask],
            generator=[
                get_permutation(
                    sequence=Sequence(move), orientate_after=True
                )
                for move in generator[1:-1].split(",")
            ],
        )
        # unpack the group of relative masks
        relative_masks = [group[0] for group in group_of_relative_masks]

        return cls([CubePattern(relative_masks=relative_masks)])

    def create_symmetries(self) -> None:
        """
        Create symmetries for the cube expression only if it has a mask.
        """
        new_patterns = []
        for pattern in self.patterns:
            new_patterns.extend(pattern.create_symmetries())
        self.patterns = new_patterns

    # TODO: Make the orientation maps into lists of indices.
    def optimize(self) -> None:
        """
        Optimize the cube expression.
        TODO: Remove idx from a orientation if it is in the mask
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
                orientation * ~pattern.mask
                for orientation in pattern.orientations
            ]
        # Remove idx in orientation if in relative mask
        for pattern in self.patterns:
            for relative_mask in pattern.relative_masks:
                pattern.orientations = [
                    orientation * ~relative_mask
                    for orientation in pattern.orientations
                ]
        # Remove idx in relative masks if in mask
        for pattern in self.patterns:
            pattern.relative_masks = [
                relative_mask * ~pattern.mask
                for relative_mask in pattern.relative_masks
            ]


@lru_cache(maxsize=1)
def get_cubexes() -> dict[str, Cubex]:
    """
    Return a dictionary of cube expressions from the tag.
    """
    cubex_dict = {}

    # Symmetric masks
    mask_tags = {
        Basic.cp_layer.value: "M' S Dw",
        Basic.ep_layer.value: "M2 D2 F2 B2 Dw",
        Basic.xp_face.value: "y",
        Basic.layer.value: "Dw",
        Basic.line.value: "L R Uw",
        CFOP.cross.value: "R L U2 R2 L2 U2 R L U",
        CFOP.f2l.value: "U",
        CFOP.x_cross.value: "R L' U2 R2 L U2 R U",
        CFOP.xx_cross_adjacent.value: "R L' U2 R' L U",
        CFOP.xx_cross_diagonal.value: "R' L' U2 R L U",
        CFOP.xxx_cross.value: "R U R' U",
        FewestMoves.block_1x1x3.value: "Fw Rw",
        FewestMoves.block_1x2x2.value: "U R Fw",
        FewestMoves.block_1x2x3.value: "U Rw",
        FewestMoves.block_2x2x2.value: "U R F",
        FewestMoves.block_2x2x3.value: "U R",
        FewestMoves.corners.value: "M' S E",
        FewestMoves.edges.value: "E2 R L S2 L R' S2 R2 S M S M'",
        FewestMoves.centers.value: "L R U D F B",
        Progress.solved.value: "",
    }
    for tag, string in mask_tags.items():
        cubex_dict[tag] = Cubex.from_solved_after_sequence(
            sequence=Sequence(string)
        )

    # Symmetric relative solved masks
    cubex_dict[CFOP.pll.value] = Cubex.from_relativly_solved(
        sequence="Dw",
        generator="<U>",
    )

    # Symmetric corner orientations
    symmetric_corner_orientation_tags = {
        Basic.co_face.value: "<U>",
    }
    for tag, gen in symmetric_corner_orientation_tags.items():
        cubex_dict[tag] = Cubex.from_generator_orientation(
            pieces=[Piece.corner],
            generator=gen,
        )

    # Symmetric edge orientations
    symmetric_edge_orientation_tags = {
        Basic.eo_face.value: "<U>",
    }
    for tag, gen in symmetric_edge_orientation_tags.items():
        cubex_dict[tag] = Cubex.from_generator_orientation(
            pieces=[Piece.edge],
            generator=gen,
        )

    # Symmetric corner and edge orientations
    symmetric_edge_corner_orientation_tags = {
        Basic.face.value: "<U>",
    }
    for tag, gen in symmetric_edge_corner_orientation_tags.items():
        cubex_dict[tag] = Cubex.from_generator_orientation(
            pieces=[Piece.corner, Piece.edge],
            generator=gen,
        )

    # Symmetric composite
    cubex_dict[Basic.face.value] = (
        cubex_dict[Basic.face.value] & cubex_dict[Basic.xp_face.value]
    )
    cubex_dict[CFOP.oll.value] = (
        cubex_dict[Basic.face.value] & cubex_dict[CFOP.f2l.value]
    )
    cubex_dict[CFOP.pll.value] = (
        cubex_dict[CFOP.f2l.value] & cubex_dict[CFOP.pll.value]
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

    # Non-symmetric relatice solved masks
    cubex_dict[FewestMoves.floppy_fb_col.value] = Cubex.from_relativly_solved(
        sequence="Dw Rw",
        generator="<L2, R2, U2, D2>",
    )
    cubex_dict[FewestMoves.floppy_lr_col.value] = Cubex.from_relativly_solved(
        sequence="Fw Dw",
        generator="<F2, B2, U2, D2>",
    )
    cubex_dict[FewestMoves.floppy_ud_col.value] = Cubex.from_relativly_solved(
        sequence="Fw Rw",
        generator="<F2, B2, L2, R2>",
    )

    # Non-symmetric edge orientations
    edge_orientation_tags = {
        FewestMoves.eo_fb.value: "<F2, B2, L, R, U, D>",
        FewestMoves.eo_lr.value: "<F, B, L2, R2 U, D>",
        FewestMoves.eo_ud.value: "<F, B, L, R, U2, D2>",
        FewestMoves.eo_fb_lr.value: "<F2, B2, L2, R2, U, D>",
        FewestMoves.eo_fb_ud.value: "<F2, B2, L, R, U2, D2>",
        FewestMoves.eo_lr_ud.value: "<F, B, L2, R2, U2, D2>",
        FewestMoves.eo_floppy_fb.value: "<L2, R2, U2, D2>",
        FewestMoves.eo_floppy_lr.value: "<F2, B2, U2, D2>",
        FewestMoves.eo_floppy_ud.value: "<F2, B2, L2, R2>",
        FewestMoves.eo_htr.value: "<F2, B2, L2, R2, U2, D2>",
    }
    for tag, gen in edge_orientation_tags.items():
        cubex_dict[tag] = Cubex.from_generator_orientation(
            pieces=[Piece.edge],
            generator=gen,
        )

    # Non-symmetric center orientations
    center_orientation_tags = {
        FewestMoves.xo_fb.value: "z",
        FewestMoves.xo_lr.value: "x",
        FewestMoves.xo_ud.value: "y",
    }
    for tag, seq in center_orientation_tags.items():
        cubex_dict[tag] = Cubex.from_solved_after_sequence(
            sequence=Sequence(seq),
            orientate_after=False,
            kind="orientation",
        )

    # Non-symmetric corner orientations
    corner_orientation_tags = {
        FewestMoves.co_fb.value: "<F, B, L2, R2, U2, D2>",
        FewestMoves.co_lr.value: "<F2, B2, L, R, U2, D2>",
        FewestMoves.co_ud.value: "<F2, B2, L2, R2, U, D>",
        FewestMoves.co_htr.value: "<F2, B2, L2, R2, U2, D2>",
    }
    for tag, gen in corner_orientation_tags.items():
        cubex_dict[tag] = Cubex.from_generator_orientation(
            pieces=[Piece.corner],
            generator=gen,
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
    cubex_dict[FewestMoves.xo_htr.value] = (
        cubex_dict[FewestMoves.xo_ud.value]
        & cubex_dict[FewestMoves.xo_fb.value]
    )
    cubex_dict[FewestMoves.dr_ud.value] = (
        cubex_dict[FewestMoves.co_ud.value]
        & cubex_dict[FewestMoves.eo_fb_lr.value]
        & cubex_dict[FewestMoves.xo_ud.value]
    )
    cubex_dict[FewestMoves.dr_fb.value] = (
        cubex_dict[FewestMoves.co_fb.value]
        & cubex_dict[FewestMoves.eo_lr_ud.value]
        & cubex_dict[FewestMoves.xo_fb.value]
    )
    cubex_dict[FewestMoves.dr_lr.value] = (
        cubex_dict[FewestMoves.co_lr.value]
        & cubex_dict[FewestMoves.eo_fb_ud.value]
        & cubex_dict[FewestMoves.xo_lr.value]
    )
    cubex_dict[FewestMoves.dr.value] = (
        cubex_dict[FewestMoves.dr_ud.value]
        | cubex_dict[FewestMoves.dr_fb.value]
        | cubex_dict[FewestMoves.dr_lr.value]
    )
    cubex_dict[FewestMoves.floppy_fb.value] = (
        cubex_dict[FewestMoves.floppy_fb_col.value]
        & cubex_dict[FewestMoves.eo_floppy_fb.value]
        & cubex_dict[FewestMoves.xo_htr.value]
    )
    cubex_dict[FewestMoves.floppy_lr.value] = (
        cubex_dict[FewestMoves.floppy_lr_col.value]
        & cubex_dict[FewestMoves.eo_floppy_lr.value]
        & cubex_dict[FewestMoves.xo_htr.value]
    )
    cubex_dict[FewestMoves.floppy_ud.value] = (
        cubex_dict[FewestMoves.floppy_ud_col.value]
        & cubex_dict[FewestMoves.eo_floppy_ud.value]
        & cubex_dict[FewestMoves.xo_htr.value]
    )
    cubex_dict[FewestMoves.floppy.value] = (
        cubex_dict[FewestMoves.floppy_fb.value]
        | cubex_dict[FewestMoves.floppy_lr.value]
        | cubex_dict[FewestMoves.floppy_ud.value]
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
        & cubex_dict[FewestMoves.eo_ud.value]
        & cubex_dict[FewestMoves.xo_ud.value]
    )
    cubex_dict[FewestMoves.leave_slice_s.value] = (
        cubex_dict[FewestMoves.minus_slice_s.value]
        & cubex_dict[FewestMoves.eo_lr.value]
        & cubex_dict[FewestMoves.xo_lr.value]
    )
    cubex_dict[FewestMoves.leave_slice_e.value] = (
        cubex_dict[FewestMoves.minus_slice_e.value]
        & cubex_dict[FewestMoves.eo_fb.value]
        & cubex_dict[FewestMoves.xo_fb.value]
    )
    cubex_dict[FewestMoves.leave_slice.value] = (
        cubex_dict[FewestMoves.leave_slice_m.value]
        | cubex_dict[FewestMoves.leave_slice_s.value]
        | cubex_dict[FewestMoves.leave_slice_e.value]
    )
    cubex_dict[FewestMoves.htr_like.value] = (
        cubex_dict[FewestMoves.co_htr.value]
        & cubex_dict[FewestMoves.eo_htr.value]
        & cubex_dict[FewestMoves.xo_htr.value]
    )

    #    OPTIMIZE    #
    for cubex in cubex_dict.values():
        cubex.optimize()

    # Sort by maximum size of mask, then by maximum size of solved pieces
    cubex_dict = dict(
        sorted(
            cubex_dict.items(), key=lambda cubex: len(cubex[1].patterns),
            reverse=True,
        ),
    )
    cubex_dict = dict(
        sorted(
            cubex_dict.items(), key=lambda cubex: max(
                sum(pattern.mask)
                for pattern in cubex[1].patterns
            ),
            reverse=True,
        )
    )
    cubex_dict = dict(
        sorted(
            cubex_dict.items(), key=lambda cubex: max(
                sum(pattern.mask) +
                max([
                    0,
                    sum([
                        sum(orientation)
                        for orientation in pattern.orientations
                    ])
                ]) +
                max([
                    0,
                    sum([
                        sum(orientation)
                        for orientation in pattern.relative_masks
                    ])
                ])
                for pattern in cubex[1].patterns
            ),
            reverse=True,
        )
    )

    return cubex_dict


def main() -> None:
    cubexes = get_cubexes()
    sequence = Sequence("F2 R2")

    print(f'\nSequence "{sequence}" tagged with {len(cubexes)} tags:\n')
    for tag, cbx in sorted(cubexes.items()):
        print(f"{tag} ({len(cbx)}):", cbx.match(sequence))
    print()

    print(cubexes["floppy-ud"].match(sequence))


if __name__ == "__main__":
    main()
