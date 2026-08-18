from __future__ import annotations

import numpy as np

from spruce.move.meta import MoveMeta
from spruce.puzzle.cube.spec import Puzzle
from spruce.transform.index import find_disjoint_subsets
from spruce.types import MoveSymbol


def groupings(labels: np.ndarray) -> set[frozenset[int]]:
    groups: dict[int, set[int]] = {}
    for index, label in enumerate(labels):
        groups.setdefault(int(label), set()).add(index)
    return {frozenset(group) for group in groups.values()}


class TestFindDisjointSubsets:
    def test_synthetic_orbits(self) -> None:
        # One 2-cycle, one 3-cycle, and two fixed points
        actions = {MoveSymbol("a"): np.array([1, 0, 3, 4, 2, 5, 6])}

        labels = find_disjoint_subsets(actions)

        assert groupings(labels) == {
            frozenset({0, 1}),
            frozenset({2, 3, 4}),
            frozenset({5}),
            frozenset({6}),
        }

    def test_labels_are_orbit_minimum(self) -> None:
        actions = {MoveSymbol("a"): np.array([1, 0, 3, 4, 2, 5, 6])}

        labels = find_disjoint_subsets(actions)

        assert labels.tolist() == [0, 0, 2, 2, 2, 5, 6]

    def test_orbits_are_closed_under_all_actions(self) -> None:
        move_meta = MoveMeta.from_puzzle(puzzle=Puzzle._3x3x3)
        actions = move_meta.get_actions(generator=frozenset({MoveSymbol("U"), MoveSymbol("R")}))

        labels = find_disjoint_subsets(actions)

        for permutation in actions.values():
            assert np.array_equal(labels, labels[permutation])
