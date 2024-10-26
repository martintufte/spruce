# Rubiks Cube Solver and Analytics Engine
![linting](https://github.com/martintufte/rubiks-cube/actions/workflows/pre-commit.yml/badge.svg)

General purpose $n \times n$ Rubik's cube solver and analytics engine.

Help is appreciated! Please reach out if you want to create an awesome app with me!

## Backlog
* Maintainace
    * [DONE] Use Google-style docstrings
    * [PROGRESS] Add missing unit tests
    * Improve the rotation solver
    * Add HTR subset recognition
    * [DONE] Use type definitions for cube states
    * Configure logging
* Finalize the bidirectional solver:
    * Use information about commutative actions to reduce effective branching factor
    * [DONE] Be able to use custom move algorithms in the solver
    * [DONE] Remove isomorphic subgroups when compiling before the solver
    * Start branching from the solved state to reduce initial branching factor for symmetrical patterns
    * Make it into a class object that returns solutions and search summary
* Ideas to solver:
    * Add possibility to match to more than one state at a time
    * Add metrics to the bidirectional solver for weighted path searching
    * Prune actions using heuristics
    * Create a custom fast inverse hash function
    * Exploit rotations and symmetries to reduce branching factor
    * Add a burn-in depth for faster solving when minimal depth is deep
    * Rust bindings for faster solver
* Implement the beam-search algorithm
    * Design functionality (async/multithreading, parameters)
    * Create multi-step solving template, template should be configurable and easy to add
* Features
    * Easy way to add patterns and algorithms for all cube sizes
    * Add a database to store solutions and algorithms
    * 3D graphics of the cube
    * Implement the official WCA scrambling generator
    * Algorithm for shortening a sequence of moves
    * API to Insertion Finder (by Baiqiang: [git](https://github.com/Baiqiang/333.fm))

## What's this?
- `pyproject.toml`: Python configuration file for system requirements, metadata and dependencies.
- `rubiks_cube/app.py`: The app that gets run by [`streamlit`](https://docs.streamlit.io/)

## Local Setup
Assumes working python 3.10 installation and some command line knowledge.

```shell
# Clone repository
git clone https://github.com/martintufte/rubiks-cube

# Navigate to the directory
cd rubiks-cube

# Create virtual environment
python -m venv .venv

# Activate the virtual environment
.\.venv\Scripts\activate  # for Windows
source ./.venv/bin/activate  # for Linux

# Install poetry
python -m pip install poetry

# Install pinned dependencies
poetry install

# Temporary patch: Navigate to the site-packages and change the st.experimental_rerun() -> st.rerun()
# on line 79 of the file .site-packages\extra_streamlit_components\Router\__init__.py

# Run the app
streamlit run rubiks_cube/app.py
```

Open your browser to [http://localhost:443/](http://localhost:443/) if it doesn't open automatically.
