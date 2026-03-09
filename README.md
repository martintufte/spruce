# Spruce 🌲

![pre-commit](https://github.com/martintufte/rubiks-cube/actions/workflows/pre-commit.yml/badge.svg)
![ci](https://github.com/martintufte/rubiks-cube/actions/workflows/ci.yml/badge.svg)

**Spruce** is a Rubik’s cube solver designed to analyse and solve phases of the cube.

Contributions are welcome! If you're interested in improving the solver, feel free to reach out.

---

## Why *Spruce*?

The name reflects both the philosophy and mechanics behind the project:

* **SPRUCE** is an acronym for **S**olving **P**atterns on the **Ru**bik’s **C**ub**e**
* To *spruce up* means to tidy or organize — much like solving a scrambled cube
* The solver is built around **tree search algorithms**
* A subtle nod to the creator’s Norwegian roots

---

## Getting Started

### Prerequisites

* Python **3.13+**
* Basic familiarity with the command line

### Installation

```bash
# Clone the repository
git clone https://github.com/martintufte/rubiks-cube

# Move into the project directory
cd rubiks-cube

# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh  # Linux/macOS/WSL

# Install dependencies
uv sync --group app
```

### Run the App

```bash
make app
```

Open your browser to [http://localhost:8501/](http://localhost:8501/)
