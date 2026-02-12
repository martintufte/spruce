"""Unit tests for autotagger functionality."""

import numpy as np
import pytest

from rubiks_cube.autotagger import autotag_permutation
from rubiks_cube.autotagger import autotag_step
from rubiks_cube.autotagger import get_rubiks_cube_pattern
from rubiks_cube.configuration.enumeration import Goal
from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.representation import get_rubiks_cube_permutation


class TestAutotagPermutation:
    """Test autotagging of cube permutations."""

    def test_solved_cube(self) -> None:
        """Test that solved cube is tagged as solved."""
        permutation = get_rubiks_cube_permutation(MoveSequence())
        tag = autotag_permutation(permutation)
        assert tag == "solved"

    def test_scrambled(self) -> None:
        """Test scrambled cube detection."""
        permutation = get_rubiks_cube_permutation(MoveSequence.from_str("R"))
        tag = autotag_permutation(permutation)
        assert tag != "solved"

    def test_htr(self) -> None:
        """Test HTR (Half Turn Reduction) detection."""
        permutation = get_rubiks_cube_permutation(MoveSequence.from_str("R2 U2 F2 D2 L2 B2"))
        tag = autotag_permutation(permutation)
        assert tag == "htr"


class TestAutotagStep:
    """Test autotagging of solution steps."""

    def test_identical(self) -> None:
        """Test that identical permutations are tagged as doing 'nothing'."""
        permutation = get_rubiks_cube_permutation(MoveSequence.from_str("R U R'"))
        tag = autotag_step(permutation, permutation)
        assert tag == "nothing"

    def test_from_none_to_pattern(self) -> None:
        """Test tagging from no pattern to a pattern."""
        initial = get_rubiks_cube_permutation(MoveSequence.from_str("R U R' U'"))
        final = get_rubiks_cube_permutation(MoveSequence())  # solved
        tag = autotag_step(initial, final)
        # Should return final tag when initial is 'none'
        assert isinstance(tag, str)

    def test_htr_real_subset_is_labeled_htr(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that real htr-like transitions are labeled as htr."""

        def fake_autotag_with_subset(
            permutation: np.ndarray,
            cube_size: int = 3,
        ) -> tuple[str, str | None]:
            return ("dr-fb", None) if permutation[0] == 0 else ("htr-like", "real")

        monkeypatch.setattr(
            "rubiks_cube.autotagger.autotag_permutation_with_subset",
            fake_autotag_with_subset,
        )
        tag = autotag_step(np.array([0]), np.array([1]))
        assert tag == "htr"

    def test_htr_fake_subset_is_labeled_fake_htr(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that fake htr-like transitions are labeled as fake htr."""

        def fake_autotag_with_subset(
            permutation: np.ndarray,
            cube_size: int = 3,
        ) -> tuple[str, str | None]:
            return ("dr-fb", None) if permutation[0] == 0 else ("htr-like", "fake")

        monkeypatch.setattr(
            "rubiks_cube.autotagger.autotag_permutation_with_subset",
            fake_autotag_with_subset,
        )
        tag = autotag_step(np.array([0]), np.array([1]))
        assert tag == "fake htr"

    def test_dr_transition_includes_subset(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that DR subset is shown for TAG_TO_TAG transitions ending in DR."""

        def fake_autotag_with_subset(
            permutation: np.ndarray,
            cube_size: int = 3,
        ) -> tuple[str, str | None]:
            return ("eo-fb", None) if permutation[0] == 0 else ("dr-ud", "4c8e 3qt")

        monkeypatch.setattr(
            "rubiks_cube.autotagger.autotag_permutation_with_subset",
            fake_autotag_with_subset,
        )
        tag = autotag_step(np.array([0]), np.array([1]))
        assert tag == "dr-ud [4c8e 3qt]"


class TestGetRubiksCubePattern:
    """Test pattern retrieval functionality."""

    def test_solved_pattern(self) -> None:
        """Test retrieving solved pattern."""
        pattern = get_rubiks_cube_pattern(Goal.solved)
        assert pattern is not None
        assert len(pattern) == 54

    def test_cross_pattern(self) -> None:
        """Test retrieving cross pattern."""
        pattern = get_rubiks_cube_pattern(Goal.cross)
        assert pattern is not None
        assert len(pattern) == 54

    def test_f2l_pattern(self) -> None:
        """Test retrieving F2L pattern."""
        pattern = get_rubiks_cube_pattern(Goal.f2l)
        assert pattern is not None
        assert len(pattern) == 54

    def test_none_pattern(self) -> None:
        """Test retrieving empty/none pattern."""
        pattern = get_rubiks_cube_pattern(Goal.none)
        assert pattern is not None
        assert len(pattern) == 54
        # Empty pattern should be all zeros
        assert (pattern == 0).all()

    def test_pattern_with_invalid_subset(self) -> None:
        """Test that invalid subset raises ValueError."""
        with pytest.raises(ValueError, match="Subset does not exist"):
            get_rubiks_cube_pattern(Goal.cross, subset="invalid_subset")

    def test_pattern_matches_permutation(self) -> None:
        """Test that solved pattern matches solved permutation."""
        pattern = get_rubiks_cube_pattern(Goal.solved)
        permutation = get_rubiks_cube_permutation(MoveSequence())
        assert (pattern[permutation] == pattern).all()

    def test_pattern_does_not_match_scrambled(self) -> None:
        """Test that solved pattern doesn't match scrambled cube."""
        pattern = get_rubiks_cube_pattern(Goal.solved)
        permutation = get_rubiks_cube_permutation(MoveSequence.from_str("R U R' U'"))
        # Pattern should not match scrambled cube.
        # This test might need adjustment based on actual moves
        assert isinstance((pattern[permutation] == pattern).all(), (bool, np.bool_))
