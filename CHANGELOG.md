# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.7.3] - 2026-07-27

### Fixed

- Fix infinite recursions in `MoveSequence.__radd__` and `Attempt.__next__`,
  idle spinning in `bidirectional_solver` when the inverse frontier is
  exhausted, and `substitute_wide_move` returning the whole input string
  instead of the matched move when no substitution applies.
- Fix app inconsistencies: write `plan_name.json` when building a solver from
  the app (plan-name persistence now lives on `ResourceHandler`, shared with
  the CLI, so UI-built solvers work with `spruce infer`), skip appending empty
  ("None") solutions to steps instead of scrubbing the text afterwards, and
  remove the Streamlit double-default warning on the steps text area.

### Changed

- Remove repeated computation: carry permutations forward and reuse
  `step_lengths` in `Attempt.compile` (was quadratic in total moves), cache
  the app's `ResourceHandler`/cattrs converter across reruns, hoist
  loop-invariant work in `filter_isomorphic_subsets`, beam search,
  `MoveMeta.pieces`, `_corner_is_bad`, and the app's `store_solutions`.
- Deduplicate logic: one `is_real_htr` validator shared by the registry and
  the htr pattern, one `find_orbit_labels` routine shared by
  `find_disjoint_subsets` and `pattern_from_generator` (replacing a fragile
  mutate-while-iterating merge; produced patterns are unchanged), `MOVE_REGEX`
  built from the compiled move patterns, aligned meet paths in
  `bidirectional_solver`, consistent session-state access in the app, and
  removed dead code (unreachable branches, redundant `__ne__`, double sort,
  `assert` used as runtime validation).

## [0.7.2] - 2026-07-17

### Changed

- Speed up `bidirectional_solver` by ~2.5x: hoist state decoding out of the
  action loop, precompute allowed successor moves from the adjacency matrix,
  and expand all successors of a state with a single batched `take` + `tobytes`.
  Solver output is unchanged.
- Speed up search-problem compilation by ~6x: vectorize `reindex` and replace
  the bidict-based bijection check in `filter_isomorphic_subsets` with plain
  forward/reverse dicts.
- Speed up `MoveMeta.get_actions` by ~5x: match expanded permutation powers via
  a serialized lookup table instead of scanning all available permutations.
- Speed up `find_disjoint_subsets` by 2-5x (growing with cube size): replace the
  quadratic python union-find with vectorized min-label propagation. Orbit
  groupings are unchanged; label values now use the orbit minimum.
- Speed up `MoveMeta.from_permutations` by 2-7x (7x on 3x3x3, ~2x on 7x7x7):
  batch pairwise move compositions against a stacked permutation matrix, derive
  commutativity from the serialized composition table, and batch rotation
  conjugations. Resulting maps are unchanged.

### Removed

- Drop the `bidict` dependency: the bijection checks in `pattern_equivalent`
  and `filter_isomorphic_subsets` now use plain forward/reverse dicts.

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
