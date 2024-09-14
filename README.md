# Rubiks Cube Solver and Analytics Engine
![linting](https://github.com/martintufte/rubiks-cube/actions/workflows/pre-commit.yml/badge.svg)

General purpose NxN Rubik's cube solver and analytics engine.

Help is appreciated! Please reach out if you want to create an awesome app with me!

## Backlog
* Maintainace
    * Use Google-style docstring everywhere
    * Add unit testing
    * Improve the rotation solver
    * Add HTR subset recognition and other subsets
* Finalize the bidirectional solver:
    * Use information about commutative actions to reduce branching factor
    * Be able to use custom move algorithms in the solver
    * Remove redundant bijective sub groups when compiling before the solver
    * Start branching from the solved state to reduce initial branching factor for symmetrical patterns
    * Change output to be json-ish with status message
* Ideas to solver:
    * Add metrics to the bi-directional solver for weighted path searching
    * Prune actions using heuristics
    * Create a custom fast inverse hash function
    * Exploit rotations and symmetries to reduce branching factor
    * Use Rust bindings to make the bi-directional solver faster
* Implement the beam-search algorithm
    * Design functionality; async? multi-threading? parameters?
    * Create multi-step solving template, template should be configurable and easy to add
* Features
    * Easy way to add patterns for all cube sizes
    * Add a Postgresql database to store solutions and personal algorithms
    * 3D graphics of the cube
    * Implement the official WCA scrambling generator
    * Algorithm for shortening a sequence of moves
    * API to Insertion Finder (by Baiqiang: [git](https://github.com/Baiqiang/333.fm))

## What's this?
- `pyproject.toml`: Python configuration file for system requirements, metadata and dependencies.
- `rubiks_cube/app.py`: The app that gets run by [`streamlit`](https://docs.streamlit.io/)
- `.streamlit/config.toml`: Customizes the behaviour of streamlit without specifying command line arguments (`streamlit config show`)

## Local Setup
Assumes working python 3.10 installation and some command line knowledge.

```shell
# External users: Download Files
git clone https://github.com/martintufte/rubiks-cube

# Navigate to directory
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
