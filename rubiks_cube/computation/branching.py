from typing import TypedDict

import numpy as np
import numpy.linalg as la

from rubiks_cube.configuration.types import BoolArray


class BranchingFactor(TypedDict):
    average: float
    expected: float
    spectral_radius: float


def compute_branching_factor(adj_matrix: BoolArray) -> BranchingFactor:
    """Compute branching factor metrics for a directed graph.

    The function interprets the boolean adjacency matrix adj_matrix as a directed graph
    with edges from node i to node j when adj_matrix[i, j] is True. It constructs
    a simple random walk transition matrix `transition_matrix`, computes the stationary
    distribution of this Markov chain, and returns several related metrics.

    Args:
        adj_matrix (BoolArray): Boolean adjacency matrix of shape (N, N).
            Must have no sink nodes (every row has at least one True entry).

    Returns:
        BranchingFactor: A dictionary containing:
            - average (float): Mean branching factor across all nodes.
            - expected (float): Expected branching factor under the stationary distribution.
            - spectral_radius (float): Largest absolute eigenvalue of the adjacency matrix.

    Notes:
        - The stationary distribution is computed as the normalized left eigenvector
          of the transition_matrix corresponding to eigenvalue 1.
        - For periodic but irreducible graphs, the stationary distribution still exists
          but the Markov chain may not converge pointwise.
    """
    # Compute branching factors (out-degrees)
    branch_factor = adj_matrix.sum(axis=1)
    if np.any(branch_factor == 0):
        raise ValueError("Adjacency matrix contains sink nodes (zero out-degree).")
    avg_branch_factor = float(branch_factor.mean())

    # Compute expected out-degree under stationary distribution
    transition_matrix = (adj_matrix.T / branch_factor).T
    vals, vecs = la.eig(transition_matrix.T)
    idx = np.argmin(np.abs(vals - 1.0))
    pi = np.real(vecs[:, idx])
    if np.sum(pi) < 0:
        pi = -pi
    pi = np.clip(pi, 0, None) / pi.sum()
    exp_branch_factor = float((pi * branch_factor).sum())

    # Compute spectral radius
    rho = float(max(np.abs(la.eigvals(adj_matrix))))

    return {
        "average": avg_branch_factor,
        "expected": exp_branch_factor,
        "spectral_radius": rho,
    }
