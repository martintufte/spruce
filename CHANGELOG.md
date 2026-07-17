# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.7.2] - 2026-07-17

### Changed

- Speed up `bidirectional_solver` by ~2.5x: hoist state decoding out of the
  action loop, precompute allowed successor moves from the adjacency matrix,
  and expand all successors of a state with a single batched `take` + `tobytes`.
  Solver output is unchanged.
- Speed up search-problem compilation by ~6x: vectorize `reindex` and replace
  the bidict-based bijection check in `filter_isomorphic_subsets` with plain
  forward/reverse dicts.

## [0.7.1] - 2026-07-17

### Changed

- Speed up `get_rubiks_cube_permutation` by ~50%: remove the sequence deepcopy,
  compose permutations with `ndarray.take`, and truncate at the first rotation
  up front instead of checking every move.
- Upgrade dependencies (numpy 2.5, matplotlib 3.11, pytest 9, black 26) and
  pre-commit hooks; move development tooling into the `dev` dependency group.
- Replace redundant pygrep hooks with ruff `PGH` rules; ignore `COM812`.

## [0.7.0] - 2026-07-16

### Changed

- Remove the `MoveSteps` abstraction (#66).
- Refactor solution representations (#65).
- Fix stale solutions display after solving (#63).
