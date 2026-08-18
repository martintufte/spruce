# TODO

This is a page to track what is being worked on, ideas and finished work

* Ideas:
  * [] EO give extra/missing solutions, e.g. run 200 solutions with scr="R' U' F L2 U B' L2 D2 F2 L D2 B2 L2 R2 D2 U' L' D R B' F' D R' U' F", the solutions should only contain (F B), not any other variants such as (F B') or (F' B).
  * [] Fix Pattern 'Floppy', the corners and edges are checked separately, but should be together
  * [] Find boundary of a move sequence
  * [] Enhancement: solve from rotated state using conjugation
  * [] Add session to store config, pruning tables and artifacts
  * [] Improve beam search; candidate alternatives
  * [] Improve bidirectional solver; add redundant moves (i.e. no visual update to pattern)
  * [] Improve beam search; subclass/coset heuristics for solving to the next step
  * [] Implement beam stack search (BSS)
  * [] Use TypeScript + FastAPI instead of Streamlit
  * [] Prune actions using heuristics/pruning tables
  * [] Solve using both normal and inverse at the same time
  * [] IDA* solver, requires pruning tables
  * [] Fix `distinguish_htr` in `autotagger/subset.py`
  * [] Unify the "solution" representation. There are currently 7 shapes: `MoveSequence`, `BeamSolution`, `RootedSolution`, `SearchSummary.solutions`, `SearchManySummary.solutions`, `cached_solutions: list[dict]`, `solutions_metadata: list[dict]`. Define a clear hierarchy and remove redundant intermediate forms.
  * [] Move algorithms to MoveMeta
  * [] Factor cube-specific code out of the algebraic core and solver
    * [] Invert the core -> cube dependencies: `solver/validators.py` owns an empty
      registry that `puzzle.cube` registers into, and `RootedSolution` carries a word
      plus side instead of a `MoveSequence`
    * [] Move packages: `representation/` -> `algebra/` plus `puzzle/cube/geometry.py`,
      `solver/`+`transform/`+`beam_search/` -> `search/`, `graphics/` -> `puzzle/cube/`
    * [] Split `MoveMeta` into a generic labelled group and a cube builder; make
      `shift_rotations_to_end` take a canonicalizer instead of the magic rotation table
    * [] Replace regex-based `measure_word` with per-symbol metric cost tables, and move
      notation parsing out of `MoveSequence.from_str` into a cube notation codec
    * [] Key search on `GoalId`/`VariantId` strings against a pattern catalogue instead of
      the `Goal`/`Variant` enums, so serialization stops reconstructing cube enums
    * [] Guard the boundary with a test that walks `algebra/` and `search/` for imports of
      `spruce.puzzle` / `spruce.autotagger`

* Progress/Done/Abandoned:
  * [DONE] Split the enums out of `configuration/enumeration.py` into `solver` and `puzzle.cube`
  * [DONE] Rename 'move' to 'symbol'
  * [DONE] Improve pattern generation: eo.fb instead of eo-fb?
  * [DONE] Rename 'Symmetry' to 'Variant' as it is not strictly a symmetry
  * [DONE] Update Pattern class to always specify variant for a goal
  * [DONE] Add support for arbitrary permutations in MoveMeta
  * [DONE] Add support for 2x2 and 4x4 in the main app
  * [DONE] Enhancement: Check if MoveMeta has move parity
  * [DONE] Bugfix: Patterns are created twice when starting the app
  * [DONE] Refactor so default generator is only using for configuration
  * [DONE] Use general knowledge derived from the permutations, not hardcoded
  * [DONE] Refactor so default cube size is only using for configuration
  * [DONE] Move pattern validator into Pattern class
  * [DONE] Rename Cubex to Pattern - more in line with name Spruce
  * [DONE] Add Symmetry.none
  * [DONE] Make the autotagger into a class
  * [DONE] Design functionality for beam solver
  * [DONE] MoveSequence stores a separate representation for normal and inverse moves
  * [DONE] Improve bidirectional solver; solve from multiple start permutations
  * [DONE] Implement the beam solver
  * [DONE] Consistent usage of 'permutation' instead of 'state'
  * [DONE] Improve beam search; add option to only search next goals if previous is contained
  * [DONE] Improve bidirectional solver; add solution_validator for distinguishing htr
  * [DONE] Improve parsing of steps; adding subsets
  * [DONE] Add MoveSteps; a sequence of steps, usually move sequences
  * [DONE] Multi-goal solving
  * [DONE] Add subsets to autotagger and solver. E.g. recognition for DR and HTR subsets
  * [DONE] Use attrs
  * [DONE] Find subset and number of moves/cancellations for solutions (show in UI)
  * [DONE] Make the bidirectional solver into a class
  * [DONE] Finalize unit tests for autotagging
  * [DONE] Finalize unit tests for move sequence, generator and algorithms
  * [DONE] Test the Schreier-Sims algorithm to find out if a state is solvable (too slow)
  * [DONE] Remove "slashed" moves
  * [DONE] Expand generator using permutations
  * [DONE] Add adjacency matrix for actions
  * [DONE] Remove old CubeState usage
  * [DONE] Remove all usages of pandas
  * [DONE] Add CI tests to Github actions
  * [DONE] Switch from mypy to ty
  * [DONE] Finalize unit tests for states, permutations and masks
  * [DONE] Switch from flake8 to ruff
  * [DONE] Rename 'state' to 'representation'
  * [DONE] Finalize unit tests for parsing of text and moves
  * [DONE] Use Google-style docstrings
  * [DONE] Bug with wide moves not being parsed properly on big cubes
  * [DONE] Use type definitions for cube state
  * [DONE] Configure logging
  * [DONE] Consistent usage of __init__.py as hierarchy for folders
  * [DONE] Switch package manager from poetry to uv
  * [DONE] Add codespell
  * [DONE] Check that a pattern is "contained" in another
  * [DONE] Return scramble, steps and final so toggling is faster in UI
  * [DONE] 10x faster calculation of "entropy"
  * [DONE] Rank patterns in auto-tagger by "entropy"
  * [DONE] Make Cubex only use CubePattern, should not need mask and pattern
  * [DONE] Add calculation of limiting branching factor
  * [DONE] Add DtypeOptimizer for patterns
  * [DONE] Prune actions using canonical move ordering
  * [DONE] Fix Integrity of the Bidirectional Solver (alternative paths)
  * [DONE] Use canonical ordering of actions for deterministic branching
  * [DONE] Use information about commutative actions to reduce effective branching factor
  * [DONE] Use information about inverse and complete actions to reduce branching factor
  * [DONE] Adaptive branching to reduce branching factor
  * [DONE] Be able to use custom move algorithms in the solver
  * [DONE] Remove isomorphic subgroups when compiling before the solver
  * [DONE] Returns solutions and search summary
  * [DONE] Scrambling. (Implement the official WCA scrambling generator or csTimer generator)
  * [ABANDONED] Enhancement: Sort with lower/upper bounds using exclusion-inclusion
  * [ABANDONED] Enhancement: Persist inverse frontier
  * [ABANDONED] Algorithm solver, requires full support for algorithms
  * [ABANDONED] Add algorithm support, e.g. :t-perm:
  * [ABANDONED] Improve parsing of steps; local updates
  * [ABANDONED] Rust bindings for faster solver
  * [ABANDONED] Improve bidirectional solver; add phase_subset for distinguishing htr
  * [ABANDONED] Database to store algorithms and attempts
  * [ABANDONED] Add symmetry class for easily configuring symmetric tags
  * [ABANDONED] Add weights to the solver for weighted searching
  * [ABANDONED] Tool for finding insertions? (E.g. [git](https://github.com/Baiqiang/333.fm))
  * [ABANDONED] Improve the rotation solver (remove magic table)
  * [ABANDONED] Tool for shortening a sequence of moves
  * [ABANDONED] Copilot to automatically complete comments
  * [ABANDONED] Exploit rotations and symmetries to reduce branching factor
  * [ABANDONED] Create a custom fast inverse hash function
  * [ABANDONED] Add a burn-in depth for faster solving when minimal depth is deep
  * [ABANDONED] Estimatation of the expected length of a solution based on pattern
  * [ABANDONED] Add inverse transformations to IndexOptimizer
