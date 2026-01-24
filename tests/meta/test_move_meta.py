import numpy as np

from rubiks_cube.meta.move import MoveMeta


def test_from_cube_size_is_cached() -> None:
    MoveMeta.from_cube_size.cache_clear()
    meta_first = MoveMeta.from_cube_size(3)
    meta_second = MoveMeta.from_cube_size(3)
    assert meta_first is meta_second


def test_basic_sets() -> None:
    meta = MoveMeta.from_cube_size(3)
    assert "I" not in meta.legal_moves
    assert "x" in meta.rotation_moves
    assert "y" in meta.rotation_moves
    assert "z" in meta.rotation_moves
    assert "x" not in meta.legal_moves
    assert "R" in meta.legal_moves


def test_compose_contains_basic_cancellations() -> None:
    meta = MoveMeta.from_cube_size(3)
    assert meta.compose[("R", "R")] == "R2"
    assert meta.compose[("R", "R'")] == ""
    assert meta.compose[("U'", "U")] == ""


def test_commutation_examples() -> None:
    meta = MoveMeta.from_cube_size(3)
    assert "L" in meta.commutes["R"]
    assert "R" in meta.commutes["L"]
    assert "U" not in meta.commutes["R"]


def test_compose_matches_permutation_product() -> None:
    meta = MoveMeta.from_cube_size(3)
    for move_a, move_b in [("R", "R"), ("U", "U2"), ("F", "F'")]:
        combined = meta.compose[(move_a, move_b)]
        perm_combined = meta.permutations[move_a][meta.permutations[move_b]]
        if combined == "":
            assert np.array_equal(perm_combined, meta.permutations["I"])
        else:
            assert np.array_equal(perm_combined, meta.permutations[combined])
