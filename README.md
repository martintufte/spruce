# Rubiks Cube Solver
![linting](https://github.com/martintufte/rubiks-cube/actions/workflows/flake8.yml/badge.svg)

General purpose NxN Rubiks Cube Solver. Solver is in early development.

Help is appreciated! Please reach out if you want to create an awesome app with me!

## Backlog
* Make this repo better by adding `pre-commit` hooks
* Add mypy unit testing
* Add version control of packages, e.g. with poetry
* Finalize the bidirectional general purpose solver
* Use Rust bindings to make a faster solver
* Add a Postgresql database to store solutions
* Add 3D rendering of the cube
* Algorithm for shortening sequence of moves
* Add API to Insertion Finder (by Baiqiang: [git](https://github.com/Baiqiang/333.fm))

## What's this?
- `requirements.txt`: Pins the version of packages needed
- `rubiks_cube/app.py`: The main app that gets run by [`streamlit`](https://docs.streamlit.io/)
- `.streamlit/config.toml`: Customizes the behaviour of streamlit without specifying command line arguments (`streamlit config show`)

## Local Setup
Assumes working python 3.10 installation and some command line knowledge.

```shell
# External users: download Files
git clone https://github.com/martintufte/rubiks-cube

# Go to correct directory
cd rubiks-cube

# Create virtual environment for this project
python -m venv .venv

# Activate the virtual environment
.\.venv\Scripts\activate  # for Windows
source ./.venv/bin/activate  # for Linux

# Install required Packages
python -m pip install -r requirements.txt

# Run the main app
streamlit run rubiks_cube/app.py
```

Open your browser to [http://localhost:443/](http://localhost:443/) if it doesn't open automatically.
