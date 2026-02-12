# AI Agent Guide for Rubik's Cube Project

## Project Overview

**Spruce** is a Rubik's cube solver built with Python and Streamlit.
It provides tools for analyzing, solving, and visualizing n x n Rubik's cubes.
Support for cube sizes 1 - 10.

### Core Features

- **Solver**: Optimized bidirectional search with pattern matching
- **Beam Search**: Beam searching from solution templates (not implemented yet)

## Quick Start

```bash
# Setup (requires Python 3.13+)
uv sync --all-groups                     # Install dependencies
uv run streamlit run rubiks_cube/app.py  # Launch web UI
uv run pytest                            # Run tests

# Code quality
uv run ruff check rubiks_cube/           # Lint
uv run ty check                          # Type check
uv run pre-commit run --all-files        # All pre-commit checks
```

## Architecture

### Module Structure

**`configuration/`** - Global settings and types

- `enumeration.py` - Enums: `Goal`, `Metric`, `Face`, `Piece`, `Symmetry`
- `types.py` - Type aliases: `CubePermutation`, `CubePattern`, `CubeMask`, etc.
- `__init__.py` - Constants: `CUBE_SIZE=3`, `METRIC=Metric.HTM`

**`move/`** - Move representation and operations

- `sequence.py` - `MoveSequence` class, sequence operations
- `generator.py` - `MoveGenerator` for action spaces
- `algorithm.py` - `MoveAlgorithm` for predefined sequences
- `metrics.py` - Move counting (HTM, QTM, STM, ETM)
- `utils.py` - Move transformations, rotations, axis operations
- `scrambler.py` - Random scramble generation

**`meta/`** - Move metadata and cached tables

- `move.py` - `MoveMeta` (legal/rotation moves, permutations, compose/commute tables)

**`representation/`** - Cube state modeling

- `permutation.py` - Permutation arrays, `create_permutations()` (LRU cached)
- `pattern.py` - Pattern arrays for matching
- `mask.py` - Boolean masks for piece selection
- `symmetries.py` - Symmetry operations
- `utils.py` - State conversions and utilities
- `__init__.py` - Main: `get_rubiks_cube_state(sequence)` → permutation

**`solver/`** - Solving algorithms

- `__init__.py` - Main: `solve_pattern()` interface
- `actions.py` - Action space generation
- `optimizers.py` - `ActionOptimizer` (adjacency matrix, LRU cached), `IndexOptimizer`, `DtypeOptimizer`
- `branching.py` - Branching factor calculations
- `rotation.py` - Solution rotation utilities
- `schreier_sims.py` - Group membership testing, `is_solvable()`, `get_group_order()`
- `bidirectional/` - Bidirectional search implementations
  - `alpha.py` - Experimental solver versions (v4-v8)
  - `beta.py` - Production solver (current default)
- `heuristics/` - Heuristic functions (in development)

**`autotagger/`** - Pattern recognition

- `__init__.py` - Main: `get_rubiks_cube_pattern(goal)`, `autotag_permutation()`
- `cubex.py` - `Cubex` class, `get_cubexes()` (LRU cached)
- `subset.py` - Subset-specific logic (HTR, DR)

**`beamsearch/`** - Beam Search (Not implemented yet)

**`formatting/`** - Text parsing and formatting

- `decorator.py` - NISS decorators: `(R)` notation
- `regex.py` - Move regex patterns
- `string.py` - String formatting utilities
- `__init__.py` - Main: `format_string_to_moves()`

**`graphics/`** - Visualization

- `__init__.py` - `get_colored_rubiks_cube()` → color array
- `horizontal.py` - `plot_cube_state()` (LRU cached), matplotlib visualization

**`experiments/`** - Benchmarking and analysis

- `solver_benchmark.py` - Solver performance comparisons

**`pages.py`** - Streamlit UI pages
**`app.py`** - Streamlit app entry point

## Key Concepts

### Data Types

- **`CubePermutation`**: `np.ndarray[np.uint]` - Permutation of 6n² stickers (n x n)
- **`CubePattern`**: `np.ndarray[np.uint]` - Pattern for matching (0=ignore)
- **`CubeMask`**: `np.ndarray[np.bool_]` - Boolean selection mask
- **`MoveSequence`**: String list representing moves
- **`MoveGenerator`**: Set of move sequences for defining actions for the solver
- **`MoveMeta`**: Cached move metadata (permutations, legal/rotation sets, compose/commute tables)

### Coordinate System

- Facelet representation (stickers on the physical cube)
- 6 faces of n² facelets = 6n² total facelets
- Face order: `[U, F, R, B, L, D]` (Up, Front, Right, Back, Left, Down)
- Permutations are index arrays where `perm[i]` = original position of sticker at position `i`

### Move Notation

- Standard: `R`, `U`, `F`, `L`, `D`, `B` (clockwise quarter turns)
- Modifiers: `R'` (counter-clockwise), `R2` (half turn)
- Wide: `Rw`, `3Rw` (multiple layers)
- Rotations: `x`, `y`, `z` (whole cube rotations)
- NISS: `(R U R')` (moves on inverse, FMC notation)
- Identities: `I` (moves), `i` (rotation)

### Pattern Matching

- Patterns use 0 for "ignore" facelets
- `pattern[permutation] == pattern` → pattern matches
- Goals like `Goal.cross`, `Goal.f2l`, `Goal.solved` map to patterns

## Performance Optimizations

### LRU Caching (functools.lru_cache)

- `create_permutations(cube_size)` - Permutation dictionary (maxsize=10)
- `get_cubexes(cube_size)` - Pattern database (maxsize=3)
- `_compute_adjacency_matrix(...)` - Adjacency matrix (maxsize=128)
- `plot_cube_state(permutation)` - Visualization (maxsize=128)

### Solver Optimizations

- **IndexOptimizer**: Renumbers stickers for cache efficiency
- **DtypeOptimizer**: Uses uint8 for patterns to reduce memory
- **ActionOptimizer**: Prunes redundant moves via adjacency matrix
- **Bidirectional search**: Searches from both start and goal simultaneously

## Development Guidelines

### Code Quality

- **Type checking**: `ty check` (strict mode, all modules typed)
- **Linting**: `ruff check --fix` (extensive rule set)
- **Formatting**: `black` (100-char lines)
- **Testing**: `pytest` (250+ tests)
- **Pre-commit**: Enforces quality on commit

### Common Patterns

**Apply moves to cube:**

```python
from rubiks_cube.representation import get_rubiks_cube_state
from rubiks_cube.move.sequence import MoveSequence

perm = get_rubiks_cube_state(MoveSequence("R U R' U'"))
```

**Create MoveMeta and cleanup:**

```python
from rubiks_cube.meta.move import MoveMeta
from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.move.sequence import cleanup

move_meta = MoveMeta.from_cube_size(3)
cleaned = cleanup(MoveSequence("R R' U2"), move_meta)
```

**Check pattern match:**

```python
from rubiks_cube.autotagger import get_rubiks_cube_pattern
from rubiks_cube.configuration.enumeration import Goal

pattern = get_rubiks_cube_pattern(Goal.cross)
matches = (pattern[perm] == pattern).all()
```

**Solve to pattern:**

```python
from rubiks_cube.solver import solve_pattern

solutions, summary = solve_pattern(
    sequence=scramble,
    goal=Goal.cross,
    max_search_depth=8
)
```

## Tech Stack

- **Language**: Python 3.13+ (strict typing)
- **Package Manager**: uv
- **UI**: Streamlit
- **Numerical**: NumPy
- **Visualization**: Matplotlib
- **Testing**: pytest
- **Quality**: ruff, ty (mypy replacement), black, pre-commit

## Debugging

- Logs: `rubiks_cube/data/logs/rubiks_cube.log` (JSON format, 5MB rotation)
- Streamlit debug: Check browser console + terminal output
- Test individual modules: `uv run python -m rubiks_cube.module_name`
- Benchmarks: `uv run python rubiks_cube/experiments/solver_benchmark.py`

## Project Status

Active development. See `TODO.md` for current tasks and backlog
