# Rubiks Cube Solver
![linting](https://github.com/martintufte/rubiks-cube/actions/workflows/flake8.yml/badge.svg)

Rubiks cube solver using streamlit, partially powered by
* NISSY (created by Sebastiano Tronto: [git](https://git.tronto.net/nissy-classic/)).

## Future ideas
* Insertion Finder (by Baiqiang: [git](https://github.com/Baiqiang/333.fm))
* Skeleton Builder and Block Builder
* Sequence Shortener

## What's this?
- `rubiks_cube/app.py`: The main app that gets run by [`streamlit`](https://docs.streamlit.io/)
- `requirements.txt`: Pins the version of packages needed
- `.gitignore`: Tells git to avoid comitting / scanning certain local-specific files
- `.streamlit/config.toml`: Customizes the behaviour of streamlit without specifying command line arguments (`streamlit config show`)

## Local Setup

Assumes working python installation and some command line knowledge.

```shell
# External users: download Files
git clone https://github.com/martintufte/rubiks-cube

# Go to correct directory
cd rubiks-cube

# Create virtual environment for this project
python -m venv venv

# Activate the virtual environment
.\venv\Scripts\activate  # for Windows
source ./venv/bin/activate  # for Linux

# Install required Packages
python -m pip install -r requirements.txt

# Create pruning tables for solving the cube using N threds
nissy gen [-t N]

# Run the main app
streamlit run rubiks_cube/app.py
```

Open your browser to [http://localhost:443/](http://localhost:443/) if it doesn't open automatically.
## Deploy

For the easiest experience, deploy to [Streamlit Cloud](https://streamlit.io/cloud)

For other options, see [Streamlit deployment wiki](https://discuss.streamlit.io/t/streamlit-deployment-guide-wiki/5099)
