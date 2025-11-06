# 🌲 Spruce - Make the cube neat again

![pre-commit](https://github.com/martintufte/rubiks-cube/actions/workflows/pre-commit.yml/badge.svg)

![ci](https://github.com/martintufte/rubiks-cube/actions/workflows/ci.yml/badge.svg)

Official implementation of Spruce, a general purpose Rubik's cube solver.
Help is appreciated! Please reach out if you want to create an awesome solver with me!

## Why *Spruce*?

* SPRUCE is an acronym for "**S**olving **P**atterns on the **Ru**bik's **C**ube".
* To *spruce* means to tidy or organize, perfecta fitting name for a solver.
* The solver uses tree search when solving.
* It also captures the Norwegian roots of the creator.

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
