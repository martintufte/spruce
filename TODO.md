# TODO

This is a page to track what is being worked on, ideas and finished work

* Backlog:
  * [] Bugfix: Patterns are created twice when starting app
  * [] Enhancement: Sort with lower/upper bounds using excludion-inclusion
  * [] Enhancement: Check if MoveMeta have move parity
  * [] Enhancement: solve from rotated state using conjugation
  * [] Enhancement: Persist inverse frontier

* Ideas:
  * [] Improve pattern generation: eo.fb instead of eo-fb?
  * [] Find boundary of a move sequence
  * [] Improve beam search; candidate variations
  * [] Improve parsing of steps; local updates
  * [] Improve bidirectional solver; add redundant moves (i.e. no visual update to pattern)
  * [] Use TypeScript + FastAPI instead of Streamlit
  * [] Prune actions using heuristics/pruning tables
  * [] Add support for 2x2 - 7x7 in the main app
  * [] Solve using both normal and inverse at the same time
  * [] Improve beam search; subclass/coset heuristics for solving to the next step
  * [] Implement beam stack search (BSS)
  * [] Add algorithm support, e.g. :t-perm:
  * [] Algorithm solver, requires full support for algorithms
  * [] IDA* solver, requires pruning tables

* Progress/Done/Abandoned:
  * [DONE] Refactor so default generarot is only using for configuration
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
  * [DONE] Use the Schreier-Sims algorithm to find out if a state is solvable (too slow)
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
