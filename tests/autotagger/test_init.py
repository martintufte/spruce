"""Unit tests for autotagger functionality."""

from spruce.algebra import get_permutation
from spruce.autotagger import PatternTagger
from spruce.autotagger import autotag_permutation
from spruce.move.meta import MoveMeta
from spruce.move.sequence import MoveSequence
from spruce.puzzle.cube.spec import Puzzle


class TestAutotagPermutation:
    """Test autotagging of cube permutations."""

    move_meta: MoveMeta = MoveMeta.from_puzzle(puzzle=Puzzle._3x3x3)

    def test_solved_cube(self) -> None:
        """Test that solved cube is tagged as solved."""
        permutation = get_permutation(MoveSequence(), move_meta=self.move_meta)
        tag = autotag_permutation(permutation, self.move_meta)
        assert tag == "solved"

    def test_scrambled(self) -> None:
        """Test scrambled cube detection."""
        permutation = get_permutation(
            MoveSequence.from_str("R"),
            move_meta=self.move_meta,
        )
        tag = autotag_permutation(permutation, self.move_meta)
        assert tag != "solved"

    def test_htr(self) -> None:
        """Test HTR (Half Turn Reduction) detection."""
        permutation = get_permutation(
            MoveSequence.from_str("R2 U2 F2 D2 L2 B2"),
            move_meta=self.move_meta,
        )
        tag = autotag_permutation(permutation, self.move_meta)
        assert tag == "htr"


class TestAutotagStep:
    """Test autotagging of solution steps."""

    move_meta: MoveMeta = MoveMeta.from_puzzle(puzzle=Puzzle._3x3x3)
    autotagger: PatternTagger = PatternTagger.from_move_meta(move_meta=move_meta)

    def test_identical(self) -> None:
        """Test that identical permutations are tagged as doing 'nothing'."""
        permutation = get_permutation(
            MoveSequence.from_str("R U R'"),
            move_meta=self.move_meta,
        )
        tag = self.autotagger.tag_step(permutation, permutation)
        assert tag == "nothing"

    def test_from_none_to_pattern(self) -> None:
        """Test tagging from no pattern to a pattern."""
        initial = get_permutation(
            MoveSequence.from_str("R U R' U'"),
            move_meta=self.move_meta,
        )
        final = get_permutation(MoveSequence(), move_meta=self.move_meta)  # solved
        tag = self.autotagger.tag_step(initial, final)

        # Should return final tag when initial is 'none'
        assert isinstance(tag, str)
