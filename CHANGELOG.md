# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed

- Fix infinite recursion in `MoveSequence.__radd__` when adding a plain
  sequence of move strings; it now builds a `MoveSequence` from the left
  operand instead of re-dispatching.
- Remove the self-recursive `Attempt.__next__`; iteration goes through the
  generator-based `__iter__`.
- Break out of `bidirectional_solver` when either frontier is exhausted,
  instead of idly spinning until `max_search_depth` once the inverse frontier
  is empty.
- Return the matched text instead of the whole input string in
  `substitute_wide_move` when no substitution applies, which would have
  duplicated text for multi-token input.
- Write `plan_name.json` when building a solver from the app, so a solver
  built via the **Build** button is usable by `spruce infer`. Plan-name
  persistence now lives on `ResourceHandler`, shared by the CLI and the app.
- Remove the Streamlit warning caused by seeding the steps text area through
  both the session state and a `value=` default.
- Skip appending empty solutions ("None") when clicking a solution in the app,
  instead of scrubbing `"None\n"` from the combined steps text afterwards.

### Changed

- Speed up `Attempt.compile`: carry each step's final permutation forward as
  the next step's initial permutation instead of re-simulating the accumulated
  sequence from the scramble, and reuse `step_lengths` instead of re-measuring
  each step in the summary and iterator.
- Cache the solver `ResourceHandler` in the app so the cattrs converter is
  built once instead of up to three times per rerun.
- Speed up `filter_isomorphic_subsets`: precompute each label's index set and
  convert the action arrays to lists once, instead of per candidate pair in
  `has_consistent_bijection`.
- Avoid duplicate `measure` calls in beam search (sort key + candidate cost)
  and hoist the loop-invariant goal pattern out of the generator loop in
  `build_step_contexts`.
- Precompute corner index arrays and expected HTR values in
  `_corner_is_bad`, and vectorize the comparison.
- Speed up `MoveMeta.pieces`: compute each move's affected indices once with
  `np.flatnonzero` and reuse them for the initial union and block splitting.
- Hoist loop-invariant work out of the per-solution loop in the app's
  `store_solutions`.
- Align the two meet paths in `bidirectional_solver`: both now pre-check root
  capacity the same way, and the always-false depth re-check on the normal
  side is removed. Solver output is unchanged.
- Use the injected session-state proxy consistently in the app instead of
  mixing it with the global `st.session_state`.
- Define the "htr is real" validator once as `is_real_htr` in
  `autotagger.subset`, shared by the validator registry and the htr pattern
  instead of two separate lambdas.
- Extract orbit labeling into `find_orbit_labels` (min-label propagation),
  shared by `find_disjoint_subsets` and `pattern_from_generator`. The latter
  previously merged labels with a fragile mutate-while-iterating loop whose
  masked-label handling was order-dependent; orbits that reach a masked index
  are now consistently mapped to the empty label. Patterns produced for all
  goals are unchanged.
- Build `MOVE_REGEX` from the five compiled move patterns instead of
  hand-maintaining a duplicate union string.
- Remove dead code: the unreachable "no solutions" warning after storing
  solutions in the app, the unreachable empty-solutions `continue` in
  `solve_pattern`, the redundant `MoveSequence.__ne__`, an overwritten
  initialization in `bidirectional_solver`, and a double sort in
  `calc_combinations`. Replace an `assert` used for runtime validation in
  `pattern_combinations` with an explicit `ValueError`.

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
