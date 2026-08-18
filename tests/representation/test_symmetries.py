from __future__ import annotations

import pytest

from spruce.puzzle.cube.variants import Variant
from spruce.representation.symmetries import find_variant_group

GROUPED_VARIANTS = [variant for variant in Variant if variant is not Variant.none]


def test_variant_group_contains_the_variant() -> None:
    """Test that every variant is a member of the group it resolves to."""
    missing = [
        variant for variant in GROUPED_VARIANTS if variant not in find_variant_group(variant)
    ]

    assert not missing


def test_variant_group_rotations_are_distinct() -> None:
    """Test that every variant in a group has its own rotation.

    Two variants sharing a rotation collapse to the same pattern, which silently
    removes one of them from the search space.
    """
    duplicates = {
        variant: group
        for variant in GROUPED_VARIANTS
        if len(set((group := find_variant_group(variant)).values())) != len(group)
    }

    assert not duplicates


def test_variant_none_has_no_group() -> None:
    """Test that a variant outside every group raises."""
    with pytest.raises(ValueError, match="not found"):
        find_variant_group(Variant.none)
