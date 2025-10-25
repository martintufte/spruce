# 🌲 Spruce - Make the cube neat again

![linting](https://github.com/martintufte/rubiks-cube/actions/workflows/pre-commit.yml/badge.svg)

Official implementation of Spruce, a general purpose Rubik's cube solver.
Help is appreciated! Please reach out if you want to create an awesome app with me!

## Why *Spruce*?

* SPRUCE is an acronym for "**S**olving **P**atterns on the **Ru**bik's **C**ube".
* The verb *spruce* means to tidy or organize, a perfect name for a solver.
* Spruce uses tree search to solve the cube.
* It also captures the Norwegian roots of the creator.

## Backlog

* Maintainace:
  * [PROGRESS] Finalize unit tests for move sequence, generator and algorithms
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
* Parser/formatter:
  * [PROGRESS] Add parsing of "slashed" moves
* Autotagger:
  * [] Finalize unit tests for tags
  * [] Add symmetry class for easily configuring symmetric tags
  * [] Estimatation of the expected length of a solution based on tag
  * [DONE] Check that a tag is "contained" in another
  * [DONE] Return scramble, steps and final so toggling is faster in UI
  * [DONE] 10x faster calculation of "entropy"
  * [DONE] Rank patterns in auto-tagger by "entropy"
  * [DONE] Make Cubex only use CubePattern, should not need mask and pattern
* Solver:
  * [] Improve the rotation solver (remove magic table)
  * [] Add inverse transformations to IndexOptimizer
  * [] Make the bidirectional solver into a class
  * [PROGRESS] Fix Integrity of the Bidirectional Solver (redundant moves)
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
* Beam-Searcher:
  * [] Design functionality and feature specifications
* Feature ideas:
  * Copilot to automatically complete comments
  * Add subsets to autotagger and solver. E.g. recognition for DR and HTR subsets
  * Multi-tag solving
  * Add metrics to the solver for weighted searching
  * Prune actions using heuristics
  * Rust bindings for faster solver
  * Use TypeScript + FastAPI instead of Streamlit
  * Database to store algorithms and attempts
  * Tool for shortening a sequence of moves
  * Tool for finding insertions? (by Baiqiang: [git](https://github.com/Baiqiang/333.fm))
  * [DONE] Scrambling. (Implement the official WCA scrambling generator or csTimer generator)
  * [ABANDONED] Exploit rotations and symmetries to reduce branching factor
  * [ABANDONED] Create a custom fast inverse hash function
  * [ABANDONED] Add a burn-in depth for faster solving when minimal depth is deep

## Local Setup

Assumes working python 3.13 installation and some command line knowledge.

```shell
# Clone repository
git clone https://github.com/martintufte/rubiks-cube

# Navigate to the directory
cd rubiks-cube

# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh  # for Linux/macOS
# or: pip install uv

# Install dependencies
uv sync --all-groups

# Run the app
uv run streamlit run rubiks_cube/app.py
```

Open your browser to [http://localhost:8501/](http://localhost:8501/) if it doesn't open automatically.
