from __future__ import annotations

from functools import lru_cache
from functools import reduce
import numpy as np

from rubiks_cube.state import get_state
from rubiks_cube.state.permutation import SOLVED_STATE
from rubiks_cube.state.permutation import get_generator_orientation
from rubiks_cube.state.permutation import create_mask
from rubiks_cube.state.permutation import generate_mask_symmetries
from rubiks_cube.utils.enumerations import Piece
from rubiks_cube.utils.enumerations import Progress
from rubiks_cube.utils.enumerations import State
from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.move.generator import MoveGenerator


class CubePattern:
    """
    Regular Cube Expression. Represents a matchable pattern.
    It consists of the following:
    - mask: A boolean mask that represents the fixed pieces to check.
    - relative_masks: A list of boolean masks that must be relative.
    - orientations: A list of boolean masks that represent the relative pieces.
    """

    def __init__(
            self,
            mask: np.ndarray | None = None,
            relative_masks: list[np.ndarray] | None = None,
            orientations: list[np.ndarray] | None = None,
    ) -> None:
        self.mask = mask if mask is not None else np.zeros_like(SOLVED_STATE, dtype=bool)  # noqa E501
        self.relative_masks = relative_masks or []
        self.orientations = orientations or []
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

    def _match_relative_masks(
        self,
        permutation: np.ndarray,
        goal: np.ndarray
    ) -> bool:
        perm_sets = [
            list(permutation[relative_mask])
            for relative_mask in self.relative_masks
        ]
        goal_sets = [
            list(goal[relative_mask_in])
            for relative_mask_in in self.relative_masks
        ]
        return all(
            any(perm_set == goal_set for goal_set in goal_sets)
            for perm_set in perm_sets
        )

    def _match_orientations(
        self,
        permutation: np.ndarray,
        goal: np.ndarray
    ) -> bool:
        return all(
            np.all(np.isin(permutation[orientation], goal[orientation]))
            for orientation in self.orientations
        )

    def match(
        self,
        permutation: np.ndarray,
        goal: np.ndarray = SOLVED_STATE
    ) -> bool:
        """
        Check if the permutation matches the pattern.
        """
        return (
            self._match_mask(permutation, goal)
            and self._match_relative_masks(permutation, goal)
            and self._match_orientations(permutation, goal)
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
        patterns: list[CubePattern],
        keep: bool = True,
    ) -> None:
        self.patterns = list(set(patterns))
        self.keep = keep

    def __repr__(self) -> str:
        return f"Cubex(patterns={self.patterns})"

    def __or__(self, other: Cubex) -> Cubex:
        """
        Combine two cube expressions with an OR operation.
        """
        return Cubex(
            patterns=[*self.patterns, *other.patterns],
            keep=self.keep or other.keep
        )

    def __ror__(self, other: Cubex) -> Cubex:
        return self | other

    def __and__(self, other: Cubex) -> Cubex:
        """
        Combine two cube expressions with an AND operation.
        Uses the cartesian product of the two sets.
        """
        return Cubex(
            patterns=[
                pattern & other_pattern
                for pattern in self.patterns
                for other_pattern in other.patterns
            ],
            keep=self.keep or other.keep
        )

    def __rand__(self, other: Cubex) -> Cubex:
        return self & other

    def __eq__(self, other: Cubex) -> bool:
        return self.patterns == other.patterns

    def __len__(self) -> int:
        return len(self.patterns)

    def match(self, input: MoveSequence | np.ndarray) -> bool:
        """
        Check if the permutation matches any of the patterns.
        """
        if isinstance(input, MoveSequence):
            permutation = get_state(sequence=input, orientate_after=False)
        else:
            permutation = input
        return any(
            pattern.match(permutation) for pattern in self.patterns
        )

    @classmethod
    def from_solved_after_sequence(
        cls,
        sequence: MoveSequence = MoveSequence(),
        invert: bool = False,
        kind: str = "permutation",
        keep: bool = True,
    ) -> Cubex:
        """
        Create a cube expression from the pieces that are solved after
        applying a sequence of moves.
        """
        mask = create_mask(sequence=sequence, invert=invert)
        if kind == "orientation":
            return cls([CubePattern(orientations=[mask])], keep=keep)
        elif kind == "permutation":
            return cls([CubePattern(mask=mask)], keep=keep)
        else:
            raise ValueError(f"Unknown kind: {kind}")

    @classmethod
    def from_generator_orientation(
        cls,
        pieces: list[Piece],
        generator: MoveGenerator,
        keep: bool = True,
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
                )
            )

        if orientations:
            return cls([CubePattern(orientations=orientations)], keep=keep)
        return cls([], keep=keep)

    @classmethod
    def from_relativly_solved(
        cls,
        sequence: str,
        generator: MoveGenerator,
        keep: bool = True,
    ) -> Cubex:
        """
        Create a cube expression from a sequence. The pieces affected by the
        sequence are considered solved. Then it will automatically find the
        pieces that are affected in the same way, i.e. the location relative to
        the other piece is the same.
        """
        mask = create_mask(sequence=sequence, invert=False)
        group_of_relative_masks = generate_mask_symmetries(
            masks=[mask],
            generator=[
                get_state(sequence=sequence, orientate_after=False)
                for sequence in generator
            ],
        )
        # unpack the group of relative masks
        relative_masks = [group[0] for group in group_of_relative_masks]

        return cls([CubePattern(relative_masks=relative_masks)], keep=keep)

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
            if len(pattern.relative_masks) > 1:
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

    # Symmetric masks to discard
    mask_tags = {
        State.xp_face.value: "y",
        State.centers.value: "L R U D F B",
    }
    for tag, string in mask_tags.items():
        cubex_dict[tag] = Cubex.from_solved_after_sequence(
            sequence=MoveSequence(string),
            keep=False,
        )

    # Symmetric masks
    mask_tags = {
        State.cp_layer.value: "M' S Dw",
        State.ep_layer.value: "M2 D2 F2 B2 Dw",
        State.layer.value: "Dw",
        State.line.value: "L R Uw",
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
        cubex_dict[tag] = Cubex.from_solved_after_sequence(
            sequence=MoveSequence(string)
        )

    # Symmetric relative solved masks
    cubex_dict[State.f2l_layer.value] = Cubex.from_relativly_solved(
        sequence="Dw",
        generator=MoveGenerator("<U>"),
    )
    cubex_dict[State.two_blocks.value] = Cubex.from_relativly_solved(
        sequence="U M",
        generator=MoveGenerator("<x>"),
    )

    # Symmetric corner orientations
    symmetric_corner_orientation_tags = {
        State.co_face.value: "<U>",
    }
    for tag, gen in symmetric_corner_orientation_tags.items():
        cubex_dict[tag] = Cubex.from_generator_orientation(
            pieces=[Piece.corner],
            generator=MoveGenerator(gen),
        )

    # Symmetric edge orientations
    symmetric_edge_orientation_tags = {
        State.eo_face.value: "<U>",
    }
    for tag, gen in symmetric_edge_orientation_tags.items():
        cubex_dict[tag] = Cubex.from_generator_orientation(
            pieces=[Piece.edge],
            generator=MoveGenerator(gen),
        )

    # Symmetric corner and edge orientations
    symmetric_edge_corner_orientation_tags = {
        State.face.value: "<U>",
    }
    for tag, gen in symmetric_edge_corner_orientation_tags.items():
        cubex_dict[tag] = Cubex.from_generator_orientation(
            pieces=[Piece.corner, Piece.edge],
            generator=MoveGenerator(gen),
        )

    # Symmetric composite
    cubex_dict[State.face.value] = (
        cubex_dict[State.face.value] & cubex_dict[State.xp_face.value]
    )
    cubex_dict[State.f2l_face.value] = (
        cubex_dict[State.face.value] & cubex_dict[State.f2l.value]
    )
    cubex_dict[State.f2l_layer.value] = (
        cubex_dict[State.f2l.value] & cubex_dict[State.f2l_layer.value]
    )
    cubex_dict[State.f2l_co.value] = (
        cubex_dict[State.co_face.value] & cubex_dict[State.f2l.value]
    )
    cubex_dict[State.f2l_eo.value] = (
        cubex_dict[State.eo_face.value] & cubex_dict[State.f2l.value]
    )
    cubex_dict[State.f2l_cp.value] = (
        cubex_dict[State.cp_layer.value] & cubex_dict[State.f2l.value]
    )
    cubex_dict[State.f2l_ep.value] = (
        cubex_dict[State.ep_layer.value] & cubex_dict[State.f2l.value]
    )
    cubex_dict[State.f2l_ep_co.value] = (
        cubex_dict[State.ep_layer.value] & cubex_dict[State.f2l_co.value]
    )
    cubex_dict[State.f2l_eo_cp.value] = (
        cubex_dict[State.eo_face.value] & cubex_dict[State.f2l_cp.value]
    )

    # Create symmetries for all cubexes defined above
    for cubex in cubex_dict.values():
        cubex.create_symmetries()

    # Non-symmetric masks
    mask_tags = {
        State.minus_slice_m.value: "M",
        State.minus_slice_s.value: "S",
        State.minus_slice_e.value: "E",
    }
    for tag, string in mask_tags.items():
        cubex_dict[tag] = Cubex.from_solved_after_sequence(
            sequence=MoveSequence(string)
        )

    # Non-symmetric relatice solved masks
    cubex_dict[State.floppy_fb_col.value] = Cubex.from_relativly_solved(
        sequence="Dw Rw",
        generator=MoveGenerator("<L2, R2, U2, D2>"),
    )
    cubex_dict[State.floppy_lr_col.value] = Cubex.from_relativly_solved(
        sequence="Fw Dw",
        generator=MoveGenerator("<F2, B2, U2, D2>"),
    )
    cubex_dict[State.floppy_ud_col.value] = Cubex.from_relativly_solved(
        sequence="Fw Rw",
        generator=MoveGenerator("<F2, B2, L2, R2>"),
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
        cubex_dict[tag] = Cubex.from_generator_orientation(
            pieces=[Piece.edge],
            generator=MoveGenerator(gen),
        )

    # Non-symmetric center orientations
    center_orientation_tags = {
        State.xo_fb.value: "z",
        State.xo_lr.value: "x",
        State.xo_ud.value: "y",
    }
    for tag, seq in center_orientation_tags.items():
        cubex_dict[tag] = Cubex.from_solved_after_sequence(
            sequence=MoveSequence(seq),
            invert=False,
            kind="orientation",
            keep=False,
        )

    # Non-symmetric corner orientations
    corner_orientation_tags = {
        State.co_fb.value: "<F, B, L2, R2, U2, D2>",
        State.co_lr.value: "<F2, B2, L, R, U2, D2>",
        State.co_ud.value: "<F2, B2, L2, R2, U, D>",
        State.co_htr.value: "<F2, B2, L2, R2, U2, D2>",
    }
    for tag, gen in corner_orientation_tags.items():
        cubex_dict[tag] = Cubex.from_generator_orientation(
            pieces=[Piece.corner],
            generator=MoveGenerator(gen),
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
    cubex_dict[State.xo_htr.value] = (
        cubex_dict[State.xo_ud.value]
        & cubex_dict[State.xo_fb.value]
    )
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
        cubex_dict[State.xx_cross_adjacent.value]
        | cubex_dict[State.xx_cross_diagonal.value]
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


def sort_patterns(cubex_dict: dict[str, Cubex]) -> dict[str, Cubex]:
    """
    Sort the patterns by the maximum size of the mask, then by the maximum size
    of the solved pieces.
    """
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
                    np.sum(reduce(np.logical_or, pattern.relative_masks))
                    if pattern.relative_masks else 0
                ])
                for pattern in cubex[1].patterns
            ),
            reverse=True,
        )
    )
    return cubex_dict


def main() -> None:
    cubexes = get_cubexes()
    sequence = MoveSequence("D R' U2 F2 D U' B2 R2 L' F U' B2 U2 F L F' D'")
    sequence += MoveSequence("x2 R' D2 R' D L' U L D R' U' R D L U' L' U' R U R' y' U R' U' R y x2")  # noqa E501

    print(f'\nMoveSequence "{sequence}" tagged with {len(cubexes)} tags:\n')
    for tag, cbx in sorted(cubexes.items()):
        print(f"{tag} ({len(cbx)}):", cbx.match(sequence))
    print()

    for state in State:
        if state.value not in cubexes:
            print(f"{state.value}")

    cubexes["f2l-layer"].match(sequence)


if __name__ == "__main__":
    main()
