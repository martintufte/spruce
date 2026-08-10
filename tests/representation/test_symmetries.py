from __future__ import annotations

import pytest

from spruce.configuration.enumeration import Variant
from spruce.representation.symmetries import find_variant_group


@pytest.mark.parametrize("variant", [variant for variant in Variant if variant is not Variant.none])
def test_variant_group_contains_the_variant(variant: Variant) -> None:
    """Test that a variant is a member of the group it resolves to."""
    assert variant in find_variant_group(variant)


@pytest.mark.parametrize("variant", [variant for variant in Variant if variant is not Variant.none])
def test_variant_group_rotations_are_distinct(variant: Variant) -> None:
    """Test that every variant in a group has its own rotation.

    Two variants sharing a rotation collapse to the same pattern, which silently
    removes one of them from the search space.
    """
    group = find_variant_group(variant)

    assert len(set(group.values())) == len(group)


def test_variant_none_has_no_group() -> None:
    """Test that a variant outside every group raises."""
    with pytest.raises(ValueError, match="not found"):
        find_variant_group(Variant.none)
