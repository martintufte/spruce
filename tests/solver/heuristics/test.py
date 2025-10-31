from __future__ import annotations

import numpy as np

from rubiks_cube.solver.heuristics import DISTANCE_TO_SOLVED


def test_distance_to_solved() -> None:
    """Test that the distance to solved heuristic has valid mean and variance."""

    dist_arr = np.array(DISTANCE_TO_SOLVED)

    mean = np.arange(len(dist_arr)) @ np.array(dist_arr) / np.sum(dist_arr)
    assert 0 <= mean <= len(dist_arr) - 1

    var = np.arange(len(dist_arr)) ** 2 @ np.array(dist_arr) / np.sum(dist_arr) - mean**2
    assert var >= 0
