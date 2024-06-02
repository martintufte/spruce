import os
import subprocess

import streamlit as st

from utils.sequence import count_length
from utils.sequence import Sequence


def execute_nissy(command, nissy_folder=".\\tools\\nissy"):
    """Execute a Nissy command using the CLI and the executable `nissy.exe`."""

    # Construct the full path to nissy.exe
    nissy_path = os.path.join(nissy_folder, "nissy.exe")
    nissy_command = f'{nissy_path} {command}'

    # Execute the command
    print(f"Executing: {nissy_command}")
    output = subprocess.run(
        nissy_command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )
    return output.stdout


def generate_random_scramble(scramble_type: str) -> str:
    """Generate a random scramble using Nissy."""

    return execute_nissy(f"scramble {scramble_type}")


def get_nissy_step(goal: str, condition: str, axis: str) -> str:
    """Get the step for Nissy."""
    steps = {
            "Optimal": {
                "from scramble": {
                    "All": "optimal",
                    "F/B": "optimal",
                    "R/L": "optimal",
                    "U/D": "optimal",
                },
                "from EO": {
                    "All": "optimal",
                    "F/B": "optimal",
                    "R/L": "optimal",
                    "U/D": "optimal",
                },
                "from DR": {
                    "All": "optimal",
                    "F/B": "optimal",
                    "R/L": "optimal",
                    "U/D": "optimal",
                },
                "from HTR": {
                    "All": "optimal",
                    "F/B": "optimal",
                    "R/L": "optimal",
                    "U/D": "optimal",
                },
            },
            "Finish": {
                "from scramble": {
                    "All": "optimal",
                    "F/B": "optimal",
                    "R/L": "optimal",
                    "U/D": "optimal",
                },
                "from EO": {
                    "All": "eofin",
                    "F/B": "eofbfin",
                    "R/L": "eorlfin",
                    "U/D": "eoudfin",
                },
                "from DR": {
                    "All": "drfin",
                    "F/B": "drfbfin",
                    "R/L": "drrlfin",
                    "U/D": "drudfin",
                },
                "from HTR": {
                    "All": "htrfin",
                    "F/B": "htrfin",
                    "R/L": "htrfin",
                    "U/D": "htrfin",
                },
            },
            "HTR": {
                "from DR": {
                    "All": "htr",
                    "F/B": "htr-drfb",
                    "R/L": "htr-drrl",
                    "U/D": "htr-drud",
                },
            },
            "DR": {
                "from scramble": {
                    "All": "dr",
                    "F/B": "drfb",
                    "R/L": "drrl",
                    "U/D": "drud",
                },
                "without breaking EO": {
                    "All": "dr-eo",
                    "F/B": "dr-eo",
                    "R/L": "dr-eo",
                    "U/D": "dr-eo",
                },
                "without breaking EO on F/B": {
                    "All": "dr-eofb",
                    "F/B": None,
                    "R/L": "drrl-eofb",
                    "U/D": "drud-eofb",
                },
                "without breaking EO on R/L": {
                    "All": "dr-eorl",
                    "F/B": "dr-eorl",
                    "R/L": None,
                    "U/D": "dr-eorl",
                },
                "without breaking EO on U/D": {
                    "All": "dr-eoud",
                    "F/B": "dr-eoud",
                    "R/L": "dr-eoud",
                    "U/D": None,
                },
            },
            "EO": {
                "from scramble": {
                    "All": "eo",
                    "F/B": "eofb",
                    "R/L": "eorl",
                    "U/D": "eoud",
                },
            },
        }
    return steps[goal][condition][axis]


def render_nissy_settings():
    """Render the settings bar for nissy."""
    n_solutions = st.slider(
        label="Number of solutions",
        min_value=1,
        max_value=20,
        value=5,
    )
    col1, col2, col3, col4 = st.columns(spec=[1.5, 1, 1, 1])
    check = col1.selectbox(
        "Check",
        options=["Normal", "Normal or Inverse", "Combination"],
        index=1,
    )
    goal = col2.selectbox(
        "Find",
        options=["EO", "DR", "HTR", "Finish", "Optimal"],
        index=0,
    )
    axis = col3.selectbox(
        "Axis",
        options=["All", "F/B", "R/L", "U/D"],
        index=0,
    )
    break_progress = col4.selectbox(
        "Can break progress",
        options=["Yes", "No"],
        index=0,
    )
    return n_solutions, goal, check, axis, break_progress


def render_tool_nissy():
    """Nissy tool."""

    # Settings
    n_solutions, goal, check, axis, break_progress = render_nissy_settings()

    # Find goal
    st.write("")
    _, col2, _ = st.columns(spec=[1, 1, 1], gap="large")
    execute = col2.button(label="Execute")
    if execute:
        with st.spinner(f"Finding {goal}..."):
            # Condition
            if goal == "Finish":
                condition = "from HTR"
            elif goal == "HTR":
                condition = "from DR"
            else:
                condition = "from scramble"

            # Flags for command
            flags = " -p"
            if check == "Normal or Inverse":
                flags += " -L"
            elif check == "Combination":
                flags += " -N"

            # Number of solutions
            if n_solutions > 1:
                flags += " -n " + str(n_solutions)

            # Run on the number of cpu threads on this computer
            n_threads = os.cpu_count()
            flags += f" -t {n_threads}"

            if goal is not None:
                step = get_nissy_step(goal, condition, str(axis))

                moves = st.session_state.scramble + st.session_state.user
                # if len(moves) > 3:
                #     st.code(f"solve {step}{flags} {str(moves[:3])} ...", language="io")  # noqa: E501
                # else:
                #     st.code(f"solve {step}{flags} {str(moves)}", language="io")  # noqa: E501
                nissy_raw = execute_nissy(f"solve {step}{flags} {str(moves)}")
                nissy_raw = nissy_raw.strip()

                # nissy output a solution
                nissy_string = ""
                for line in nissy_raw.split("\n"):
                    if not line.strip() == "":
                        nissy_moves = Sequence(line)

                        # combined moves
                        combined = st.session_state.user + nissy_moves
                        combind_string = str(combined)
                        combind_string = execute_nissy(f"unniss {combind_string}")  # noqa: E501
                        combind_string = execute_nissy(f"cleanup {combind_string}")  # noqa: E501
                        combined = Sequence(combind_string)

                        # length of moves
                        m_len = count_length(st.session_state.user)
                        n_len = count_length(nissy_moves)
                        com_len = count_length(combined)
                        diff = m_len + n_len - com_len

                        if diff:
                            comment = f" // {goal} ({n_len}-{diff}/{com_len})"
                        elif m_len == 0:
                            comment = f" // {goal} ({n_len})"
                        else:
                            comment = f" // {goal} ({n_len}/{com_len})"

                        nissy_string += "\n" + str(nissy_moves) + comment
                    else:
                        nissy_string += f"Could not find {goal}!"
                        n_solutions = 1

                # Write Nissy output
                st.text_area("Output", value=nissy_string.strip(), height=n_solutions * 23 + 25)  # noqa: E501


class Nissy():
    """ Nissy class. """
    def __init__(self):
        self.name = "Nissy"
        pass

    def render(self):
        render_tool_nissy()

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name
