# Design Audit — Action Items

This file was generated from a full design audit of the repository. Items are grouped by area.
Each item names the specific file and location. Work through these one by one; check them off as done.

---

## Beam search core (`beam_search/solver.py`)

- [x] Remove the `expand_candidate` dead plumbing. The function at line 127 is a no-op stub that returns `[candidate]`. All the `candidate_alternatives` / `permutation_index` machinery in the search loop (lines 280–321) is built around it and contributes nothing. Delete the stub, collapse `candidate_alternatives = [candidate]` away, and simplify the loop.
- [x] Fix `select_top_k` (line 111): the sort key is `(candidate.cost, candidate.cost)` — both slots are identical. Give the secondary key a meaningful value (e.g. step count) or collapse to a single key.
- [x] Fix `search_sides` (line 62): `"both"` is not listed as an explicit branch; it is reached by falling through all other checks. Add an explicit `if step.transition.search_side == "both":` branch and a `raise ValueError(...)` for any unrecognized value.
- [x] Fix `_inverse_frontier_cache` key in `BidirectionalSolver._get_inverse_frontier` (`solver/bidirectional/__init__.py` line 89): the cache is keyed by `max_search_depth` but built to `max_search_depth // 2`. Querying depth 10 then depth 11 builds two identical caches. Key on the actual built depth (`max_search_depth // 2`) instead.
- [x] Remove the unused `_transition_goal` return value at line 286: `transition_prev_goal` returns `(goal, variant)` but the goal is always discarded. Simplify the accessor to return only the variant, or add a separate `transition_prev_variant` method.
- [x] Rename `StepOptions` → `CompiledStep` and `StepContext` → `CompiledVariant` throughout `solver.py`, `converter.py`, and `resources.py`. The name "options" implies user-configurable parameters; these are compiled/built search structures.
- [x] Replace `str(generator)` dict key in `contexts_for_prev_variant` (line 97) and in `build_step_contexts` (line 146) with a stable identity (e.g. a `frozenset` of move names). String-formatting is fragile against changes in `MoveGenerator.__str__`.
- [x] Remove `min_search_depth` from `beam_search`, `StepOptions`, `BeamStep`, and the `BidirectionalSolver.search` call chain. It is always 0 in every plan and every call site — dead parameter plumbing.
- [x] Tighten the `max_time` check: currently checked per-candidate (line 274) but not per-side. A single candidate with many variants × both sides can silently exceed `max_time`.

---

## Beam plans (`beam_search/plan.py`)

- [x] Compose plans from shared `BeamStep` constants instead of copy-pasting. Define named constants (`EO_STEP`, `DR_STEP`, `HTR_STEP`, `FINISH_STEP`) and build each plan by referencing them: `DR_PLAN = [EO_STEP, DR_STEP]`, `HTR_PLAN = [EO_STEP, DR_STEP, HTR_STEP]`, etc. Currently, tuning one step's depth requires edits in up to four places.
- [x] Fix the HTR step `generator_map` key order inconsistency between `HTR_PLAN` (line 79: lr/ud/fb) and `SOLVED_PLAN` (line 129: lr/fb/ud) — copy-paste drift. After the above refactor this goes away automatically.
- [x] Fix `LEAVE_SLICE_PLAN`'s leave-slice step (lines 227–230): all three `generator_map` keys map to the identical generator `<L2, R2, F2, B2, U2, D2>`. Either the generators should differ per axis (likely a bug) or the dict should collapse to a single key under `Variant.none`.
- [x] Replace the `BEAM_PLANS` string-key dict (line 245) with an `Enum`-keyed structure to prevent name collisions and make plan selection type-safe in callers.

---

## Transition type (`beam_search/interface.py`)

- [x] Replace `search_side: Literal["prev", "normal", "inverse", "switch", "both"]` with a small `SearchSideChoice` enum. `SearchSide` already exists as an enum for runtime use; having a parallel string-literal domain for the same concept is confusing.
- [x] Document (or restructure) the dual semantics of `generator_map`: for the first step the key is `Variant.none` (source); for later steps the key is the previous step's variant. This is discovered only by reading `transition_prev_goal` / `contexts_for_prev_variant` in `solver.py`. Add a class-level docstring or split into two fields.
- [x] Replace `prev_goal_index: int = -1` with a documented bounded type or a small enum (e.g. `PrevGoalRef.last | PrevGoalRef.second_last`). Arbitrary integer indexing into `goal_history` with no bounds check is unsafe.
- [x] Add validation to `Transition.__attrs_post_init__` (or a factory): check that `search_side` is a recognized value, that `generator_map` is non-empty, and that `prev_goal_index` is in a safe range.
- [x] Note: `BeamPlan.steps: list[BeamStep]` is mutable despite `attrs.frozen`. Change to `tuple[BeamStep, ...]` so the plan is truly immutable at runtime.

---

## BidirectionalSolver (`solver/bidirectional/__init__.py`)

- [x] Resolve the `_inverse_frontier_cache` / `@attrs.frozen` inconsistency (lines 40–42). Either move the cache to a module-level `functools.lru_cache`-style helper (keeping the class truly immutable) or drop `@attrs.frozen` and use `@attrs.define`. The current approach is acknowledged in a comment as inconsistent.
- [x] Remove `validator` from `BidirectionalSolver` fields and resolve it from `validator_key` via the registry at call time. Storing both a callable and a string id leaks serialization concerns into the domain object (`solver/bidirectional/__init__.py` lines 39, 50).
- [x] Document the invariant that `optimize_indices` is silently disabled when `validator is not None` (line 55). Either raise an explicit error when a caller passes `optimize_indices=True` with a validator, or add a docstring explaining why this downgrade happens.
- [x] Consolidate `SearchSide.inverse` handling: the inversion of input permutations and re-wrapping of output as `MoveSequence(inverse=...)` (lines 108–115, 144–147) duplicates what permutation composition already handles. Move the inversion to one place.

---

## Bidirectional solver internals (`solver/bidirectional/beta.py`)

- [ ] Clarify the `use_fixed_inverse` branch logic. The `if use_fixed_inverse or len(normal_frontier) < len(inverse_frontier): ... elif not use_fixed_inverse and inverse_frontier:` pattern is hard to follow. Separate the fixed-frontier path from the adaptive path clearly.
- [ ] Remove the misleading `alternative_inverse_paths = {}` initialization (line 145) when `prebuilt_inverse_frontier` is used — it is never populated in that code path but still referenced in the bridge at line 193. Either populate it or remove the reference.
- [ ] Reorder checks in `add_solution`: validate whether the root is full *before* running the validator, not after (line 102). Currently, validator work is done and then discarded when the root is already full.
- [ ] Deduplicate `solved_bytes = pattern.tobytes()`: computed in both `bidirectional_solver` (line 82) and `precompute_inverse_frontier` (line 31). Factor into a shared setup step or pass it in.

---

## Dead code

- [ ] Delete `solver/bidirectional/alpha.py`. It exists only to support `experiments/solver_benchmark.py`, which benchmarks a different code path than production uses. Move any still-relevant benchmark logic to use `BidirectionalSolver` directly, then delete `alpha.py`.
- [ ] Delete `solver/ida_star/__init__.py`. It is a 2-line comment stub with no implementation.
- [ ] Delete `UnsolveableError` from `solver/interface.py`. It is defined but never raised or caught anywhere in the codebase.
- [ ] Remove `SolveStrategy` and its conversion to `SearchSide` in `solver/__init__.py` (lines 111–116). `SearchSide` already covers the same concept. Migrate all callers to use `SearchSide` directly.
- [ ] Audit the `Goal` enum (`configuration/enumeration.py`). Remove members that have no corresponding pattern in `autotagger/pattern.py` and no reference in the autotagger or solver. The enum currently has ~50 members; many are unused.

---

## Serialization (`serialization/converter.py`, `serialization/resources.py`)

- [ ] Remove the module-scope imports of `StepContext` and `StepOptions` from `rubiks_cube.beam_search.solver` in `converter.py` (lines 14–15). The serialization package should not depend on beam-search solver internals. Move serialization schemas for these types to a dedicated `beam_search/schema.py` or use forward refs.
- [ ] Fix `_structure_transition` in `converter.py` (line 117): `search_side` is read as `data["search_side"]` (will `KeyError` on old data) while all other fields use `.get(..., default)`. Make it consistent.
- [ ] Make unknown `validator_key` fail loudly in `_structure_solver` (line 169). Currently silently falls back to `validator=None`, which changes search correctness without any warning.
- [ ] Add a schema version field to the serialized JSON so that field renames or additions are detected on load rather than silently loading stale defaults.
- [ ] Split `ResourceHandler` into separate, focused objects (or functions) — it currently manages three unrelated domains (`config`, `pipeline`, `step_contexts`). Also remove the `mkdir` side-effect from `__attrs_post_init__`; callers that only read shouldn't trigger directory creation.
- [ ] Fix the two runtime-local imports in `resources.py` (lines 54, 68) that exist to avoid circular imports (`# noqa: PLC0415`). These indicate the module layering is off — fix the layering instead of using local imports as a workaround.

---

## Pages / UI (`pages.py`)

- [ ] Break up the `app()` god function (~300 lines). Extract at minimum: `run_standard_solve(...)`, `run_beam_build(...)`, `run_beam_solve(...)`, and `render_solution_list(...)`. The page function should only read inputs, call these, and render results.
- [ ] Move all domain computation out of `store_solutions` (lines 139–244): applying the scramble, computing permutations, autotagging, measuring cancellations, unnissing. These belong in a service layer, not in the UI file.
- [ ] Deduplicate the "store solutions" flow: the logic for `solve_clicked` (lines 432–449) and `beam_solve_clicked` (lines 472–494) is near-identical. Unify into one `store_solutions` call path.
- [ ] Fix the cookie / session-state dual source of truth. `raw_steps`, `raw_scramble`, and `solver_solutions` live in both; `raw_steps_pending` is a workaround for Streamlit re-run semantics. Establish one authoritative source (cookies as write-through, session state as read cache) with a single reconciliation point at page load.
- [ ] Replace `assert isinstance(moves, int)` (line ~509) in the render path with a proper guard that discards or logs malformed cookie data instead of crashing.
- [ ] Replace the `10**9` sort-key sentinel (lines 223–225) with `math.inf` or a typed sentinel so intent is clear and numeric overflow is impossible.
- [ ] Cache `attempt.compile(autotagger, width=80)` (line ~279) by scramble + steps hash — it is recomputed on every Streamlit rerun.

---

## Configuration / Representation

- [ ] Change `AppConfig.log_level` default from `"debug"` to `"warning"` (`configuration/__init__.py` line 27). Debug logging is too chatty for a user-facing Streamlit app.
- [ ] Split `get_rubiks_cube_permutation` (`representation/__init__.py` lines 20–26) into focused functions: `apply_sequence(seq, move_meta)` and `apply_inverted_sequence(seq, move_meta)`. The current function has 6 parameters and 4 modes driven by boolean flags.
- [ ] Remove `get_identity_permutation` from `representation/permutation.py` — it is a dead alias that delegates directly to `get_identity` in `utils.py`. Pick one name and delete the other.
- [ ] Add a check in `reindex` (`representation/utils.py` line 77) that the invariant `perm[~mask] == id[~mask]` holds, or at least document it prominently. Violating it silently corrupts the permutation.
- [ ] Reconsider `MoveSequence`'s normal/inverse two-list design (`move/sequence.py`). The slicing logic has 6 branches to avoid crossing the boundary. A single list with side markers would simplify `__getitem__`, `__iter__`, `__len__`, and all slice operations.

---

## Autotagger (`autotagger/`)

- [ ] Fix the `"fake htr"` vs `Goal.fake_htr.value` mismatch. `PatternTagger.tag_with_subset` uses the literal string `"fake htr"` (space), but `Goal.fake_htr.value == "fake-htr"` (dash). Tags silently fail to map to display steps. Replace the literal with `Goal.fake_htr.value`.
- [ ] Fix `TAG_TO_TAG_STEPS` in `autotagger/step.py`: keys mix `Goal.value` strings with `"fake htr"` which doesn't match any enum value. Audit all keys and replace literals with `Goal.<member>.value`.
- [ ] Fix `distinguish_htr` in `autotagger/subset.py` (line ~152): it uses stochastic random moves to classify HTR state. A TODO acknowledges this is wrong. Replace with a deterministic classification based on the permutation structure.
- [ ] Fix the type-flip in `get_dr_subset_label` (`autotagger/subset.py`): `qt` is set to `2` (int) in one branch and `"3"` (str) in another. Make the type consistent throughout.
- [ ] Fix `Attempt.compile` (`autotagger/attempt.py` line ~125): it recomputes `sum(self.steps[:i], ...)` in a loop — O(n²) in step count. Compute incrementally instead.
- [ ] Remove the global `Lock` in `autotagger/pattern.py` (line ~40). Streamlit does not spawn threads for page renders; the lock is over-engineering and adds noise.

---

## Cross-cutting

- [ ] Unify the "solution" representation. There are currently 7 shapes: `MoveSequence`, `BeamSolution`, `RootedSolution`, `SearchSummary.solutions`, `SearchManySummary.solutions`, `cached_solutions: list[dict]`, `solutions_metadata: list[dict]`. Define a clear hierarchy and remove redundant intermediate forms.
- [ ] Introduce an explicit `Cost` type (or at minimum a named alias) rather than passing raw `int` everywhere for move counts. `BeamSearchSummary` currently carries no cost; `BeamSolution` carries one but it is always derived — standardize.
- [ ] Fix enum value naming consistency: `Status` uses PascalCase (`Success`/`Failure`), `SearchSide` uses lowercase (`normal`/`inverse`), `Goal` uses snake_case. Pick one convention and apply it across all enums in `configuration/enumeration.py`.
- [ ] Remove `DEFAULT_GENERATOR_MAP` entries for cube sizes that have no pattern implementation (only size 3 is implemented). Dead entries in a constants map cause confusion.
