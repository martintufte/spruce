from typing import TYPE_CHECKING

import numpy as np
import pytest

from rubiks_cube.solver.branching import compute_branching_factor

if TYPE_CHECKING:
    from rubiks_cube.configuration.types import BoolArray


class TestComputeBranchingFactor:
    @pytest.mark.parametrize("size", [1, 2, 6, 10, 18])
    def test_full_matrix(self, size: int) -> None:
        adj_matrix: BoolArray = np.ones((size, size), dtype=bool)

        stats = compute_branching_factor(adj_matrix)

        assert np.isclose(stats["average"], size)
        assert np.isclose(stats["expected"], size)
        assert np.isclose(stats["spectral_radius"], size)

    @pytest.mark.parametrize("size", [3, 6, 10, 18])
    def test_cycle_graph(self, size: int) -> None:
        adj_matrix: BoolArray = np.zeros((size, size), dtype=bool)
        for i in range(size):
            adj_matrix[i, (i + 1) % size] = True

        stats = compute_branching_factor(adj_matrix)

        assert np.isclose(stats["average"], 1.0)
        assert np.isclose(stats["expected"], 1.0)
        assert np.isclose(stats["spectral_radius"], 1.0)

    def test_sink_node_raises(self) -> None:
        adj_matrix: BoolArray = np.array(
            [
                [False, True, True],
                [False, False, False],
                [True, True, False],
            ],
            dtype=bool,
        )

        with pytest.raises(ValueError, match="sink nodes"):
            compute_branching_factor(adj_matrix)

    def test_asymmetric_graph(self) -> None:
        adj_matrix: BoolArray = np.array(
            [
                [False, True, True, False],
                [False, False, True, True],
                [True, False, False, True],
                [True, True, False, False],
            ],
            dtype=bool,
        )

        stats = compute_branching_factor(adj_matrix)

        assert np.isclose(stats["average"], 2.0)
        assert np.isclose(stats["expected"], 2.0)
        assert np.isclose(stats["spectral_radius"], 2.0)

    def test_irreducible_periodic_graph(self) -> None:
        adj_matrix: BoolArray = np.array(
            [
                [False, True, False, False],
                [False, False, True, False],
                [False, False, False, True],
                [True, False, False, False],
            ],
            dtype=bool,
        )

        stats = compute_branching_factor(adj_matrix)

        assert np.isclose(stats["average"], 1.0)
        assert np.isclose(stats["expected"], 1.0)
        assert np.isclose(stats["spectral_radius"], 1.0)

    def test_large_sparse_graph(self) -> None:
        size = 100
        adj_matrix: BoolArray = np.zeros((size, size), dtype=bool)
        for i in range(size):
            adj_matrix[i, (i + 1) % size] = True
            adj_matrix[i, (i + 2) % size] = True

        stats = compute_branching_factor(adj_matrix)

        assert np.isclose(stats["average"], 2.0)
        assert np.isclose(stats["expected"], 2.0)
        assert np.isclose(stats["spectral_radius"], 2.0)

    def test_two_node_bidirectional_graph(self) -> None:
        adj_matrix: BoolArray = np.array(
            [
                [False, True],
                [True, False],
            ],
            dtype=bool,
        )

        stats = compute_branching_factor(adj_matrix)

        assert np.isclose(stats["average"], 1.0)
        assert np.isclose(stats["expected"], 1.0)
        assert np.isclose(stats["spectral_radius"], 1.0)
