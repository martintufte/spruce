"""Unit tests for autotagger functionality."""

import numpy as np
import pytest

from rubiks_cube.autotagger import PatternTagger
from rubiks_cube.autotagger import autotag_permutation
from rubiks_cube.move.meta import MoveMeta
from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.representation import get_rubiks_cube_permutation


class TestAutotagPermutation:
    """Test autotagging of cube permutations."""

    move_meta: MoveMeta = MoveMeta.from_cube_size(3)

    def test_solved_cube(self) -> None:
        """Test that solved cube is tagged as solved."""
        permutation = get_rubiks_cube_permutation(MoveSequence(), move_meta=self.move_meta)
        tag = autotag_permutation(permutation, self.move_meta.cube_size)
        assert tag == "solved"

    def test_scrambled(self) -> None:
        """Test scrambled cube detection."""
        permutation = get_rubiks_cube_permutation(
            MoveSequence.from_str("R"), move_meta=self.move_meta
        )
        tag = autotag_permutation(permutation, self.move_meta.cube_size)
        assert tag != "solved"

    def test_htr(self) -> None:
        """Test HTR (Half Turn Reduction) detection."""
        permutation = get_rubiks_cube_permutation(
            MoveSequence.from_str("R2 U2 F2 D2 L2 B2"), move_meta=self.move_meta
        )
        tag = autotag_permutation(permutation, self.move_meta.cube_size)
        assert tag == "htr"


class TestAutotagStep:
    """Test autotagging of solution steps."""

    move_meta: MoveMeta = MoveMeta.from_cube_size(3)
    autotagger: PatternTagger = PatternTagger.from_cube_size(3)

    def test_identical(self) -> None:
        """Test that identical permutations are tagged as doing 'nothing'."""
        permutation = get_rubiks_cube_permutation(
            MoveSequence.from_str("R U R'"), move_meta=self.move_meta
        )
        tag = self.autotagger.tag_step(permutation, permutation)
        assert tag == "nothing"

    def test_from_none_to_pattern(self) -> None:
        """Test tagging from no pattern to a pattern."""
        initial = get_rubiks_cube_permutation(
            MoveSequence.from_str("R U R' U'"), move_meta=self.move_meta
        )
        final = get_rubiks_cube_permutation(MoveSequence(), move_meta=self.move_meta)  # solved
        tag = self.autotagger.tag_step(initial, final)
        # Should return final tag when initial is 'none'
        assert isinstance(tag, str)

    def test_htr_real_subset_is_labeled_htr(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that real htr-like transitions are labeled as htr."""

        def fake_tag_with_subset(
            self: PatternTagger,
            permutation: np.ndarray,
        ) -> tuple[str, str | None]:
            return ("dr-fb", None) if permutation[0] == 0 else ("htr", None)

        monkeypatch.setattr(PatternTagger, "tag_with_subset", fake_tag_with_subset)
        tag = self.autotagger.tag_step(np.array([0]), np.array([1]))
        assert tag == "htr"

    def test_htr_fake_subset_is_labeled_fake_htr(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that fake htr-like transitions are labeled as fake htr."""

        def fake_tag_with_subset(
            self: PatternTagger,
            permutation: np.ndarray,
        ) -> tuple[str, str | None]:
            return ("dr-fb", None) if permutation[0] == 0 else ("fake htr", None)

        monkeypatch.setattr(PatternTagger, "tag_with_subset", fake_tag_with_subset)
        tag = self.autotagger.tag_step(np.array([0]), np.array([1]))
        assert tag == "fake htr"
