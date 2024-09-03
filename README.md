# Rubiks Cube Solver
![linting](https://github.com/martintufte/rubiks-cube/actions/workflows/pre-commit.yml/badge.svg)

General purpose NxN Rubik's cube solver.

Help is appreciated! Please reach out if you want to create an awesome app with me!

## Backlog
* Add unit testing and more pre-commit hooks
* Finalize the bidirectional solver
* Easy way to add patterns for all cube sizes
* Use Rust bindings to make an even faster solver
* Add a Postgresql database to store solutions
* Add 3D rendering of the cube
* Add rubiks cube state pruning
* Tool idea: Algorithm for shortening sequence of moves
* Add API to Insertion Finder (by Baiqiang: [git](https://github.com/Baiqiang/333.fm))

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

# Run the app
streamlit run rubiks_cube/app.py
```

Open your browser to [http://localhost:443/](http://localhost:443/) if it doesn't open automatically.
