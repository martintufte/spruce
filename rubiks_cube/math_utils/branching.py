from typing import TypedDict

import numpy as np
from numpy.linalg import eig
from numpy.linalg import eigvals

from rubiks_cube.configuration.types import BoolArray


class GraphStats(TypedDict):
    """Return type for compute_stationary_and_branching."""

    p: np.ndarray
    stationary: np.ndarray
    avg_out_degree: float
    expected_out_degree_under_stationary: float
    adjacency_spectral_radius: float


def compute_stationary_and_branching(adj: BoolArray, tol: float = 1e-12) -> GraphStats:
    """Compute stationary distribution and branching metrics for a directed graph.

    The function interprets the boolean adjacency matrix `adj` as a directed graph
    with edges from node *i* to node *j* when `adj[i, j]` is True. It constructs
    a simple random walk transition matrix `p`, computes the stationary
    distribution of this Markov chain, and returns several related metrics.

    Args:
        adj (BoolArray): Boolean adjacency matrix of shape (N, N).
            Must have no sink nodes (every row has at least one True entry).
        tol (float, optional): Numerical tolerance for eigenvalue selection.
            Defaults to 1e-12.

    Returns:
        GraphStats: A dictionary containing:
            - **p** (`np.ndarray`): Row-stochastic transition matrix.
            - **stationary** (`np.ndarray`): Stationary distribution vector π.
            - **avg_out_degree** (`float`): Mean out-degree across all nodes.
            - **expected_out_degree_under_stationary** (`float`):
              Expected out-degree weighted by stationary distribution.
            - **adjacency_spectral_radius** (`float`):
              Largest absolute eigenvalue of the adjacency matrix (effective branching factor).

    Notes:
        - The stationary distribution is computed as the normalized left
          eigenvector of `p` corresponding to eigenvalue 1.
        - For periodic but irreducible graphs, the stationary distribution
          still exists but the Markov chain may not converge pointwise.
        - For large sparse matrices, consider using
          `scipy.sparse.linalg.eigs` instead of dense eigen-decomposition.
    """
    k = adj.sum(axis=1)  # out-degrees (shape (N,))
    p = adj / k[:, None]  # row-stochastic matrix

    # Compute left eigenvector for eigenvalue ~1
    vals, vecs = eig(p.T)
    idx = np.argmin(np.abs(vals - 1.0))
    pi = np.real(vecs[:, idx])
    pi = np.maximum(pi, 0)  # numerical safety
    pi = pi / pi.sum()

    avg_out_deg = float(k.mean())
    exp_out_deg = float((pi * k).sum())
    rho = float(max(np.abs(eigvals(adj))))

    return {
        "p": p,
        "stationary": pi,
        "avg_out_degree": avg_out_deg,
        "expected_out_degree_under_stationary": exp_out_deg,
        "adjacency_spectral_radius": rho,
    }
