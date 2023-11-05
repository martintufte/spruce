# Rubiks cube
![linting](https://github.com/martintufte/rubiks-cube/actions/workflows/flake8.yml/badge.svg)

Rubiks cube applications using streamlit and LaTex

## What's this?

- `streamlit_app.py`: The main app that gets run by [`streamlit`](https://docs.streamlit.io/)
- `LaTeX-visualizer`: Folder for visualizing rubiks cubes using LaTeX
- `requirements.txt`: Pins the version of packages needed
- `.gitignore`: Tells git to avoid comitting / scanning certain local-specific files
- `.streamlit/config.toml`: Customizes the behaviour of streamlit without specifying command line arguments (`streamlit config show`)

## Local Setup

Assumes working python installation and some command line knowledge ([install python with conda guide](https://tech.gerardbentley.com/python/beginner/2022/01/29/install-python.html)).

```shell
# External users: download Files
gh repo clone martintufte/rubiks-cube

# Go to correct directory
cd rubiks-cube

# Create virtual environment for this project
python3.11 -m venv venv

# Activate the virtual environment
source ./venv/bin/activate
# .\venv\Scripts\activate for Windows

# Install required Packages
python -m pip install -r requirements.txt

# Run the streamlit app
streamlit run streamlit_app.py
```

Open your browser to [http://localhost:8501/](http://localhost:8501/) if it doesn't open automatically.
## Deploy

For the easiest experience, deploy to [Streamlit Cloud](https://streamlit.io/cloud)

For other options, see [Streamlit deployment wiki](https://discuss.streamlit.io/t/streamlit-deployment-guide-wiki/5099)
