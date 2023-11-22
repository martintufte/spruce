import subprocess
import streamlit as st
from utils.rubiks_cube import count_length


def execute_nissy(command):
    """Execute a Nissy command."""
    nissy_command = f"nissy {command}"

    output = subprocess.run(
        nissy_command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )

    return output.stdout


def render_nissy_settings():
    """Render the settings bar for nissy."""
    col1, col2, col3, col4 = st.columns(4)
    keep_progress = col1.toggle(
        label="Keep progress",
        value=True,
        key="keep_progress",
    )
    all_solutions = col2.toggle(
        label="All solutions",
        value=False,
        key="all_solutions",
    )
    return keep_progress, all_solutions


def render_nissy_buttons():
    """Render the action bar."""
    col1, col2, col3, col4 = st.columns(4)
    find_eo = col1.button(
        label="Find EO"
    )
    find_dr = col2.button(
        label="Find DR"
    )
    find_htr = col3.button(
        label="Find HTR"
    )
    find_rest = col4.button(
        label="Find finish"
    )
    return find_eo, find_dr, find_htr, find_rest


def render_tool_nissy():
    """Nissy tool."""

    # Settings
    keep_progress, all_solutions = render_nissy_settings()

    # Check
    check = st.selectbox(
        "Check",
        options=["Normal", "Normal or Inverse", "Combination"],
        index=1,
    )

    # Axis of choice
    axis = st.selectbox(
        "Axis",
        options=["All", "F/B", "R/L", "U/D"],
        index=0,
    )

    # Goal
    find_eo, find_dr, find_htr, find_rest = render_nissy_buttons()
    goal = None

    if find_eo:
        goal = "EO"
    elif find_dr:
        goal = "DR"
    elif find_htr:
        goal = "HTR"
    elif find_rest:
        goal = "Finish"

    steps = {
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
    else:
        pass

    if all_solutions:
        flags += " -a"

    if goal is not None:
        step = steps[goal][condition][axis]

        with st.spinner(f"Finding {goal}..."):
            moves = " ".join([
                st.session_state.scramble.moves,
                st.session_state.user.moves
            ])
            st.write(moves)
            st.write(f"solve {step}{flags} {moves}")
            nissy_raw = execute_nissy(f"solve {step}{flags} {moves}")

            st.write(nissy_raw)

            nissy_raw = nissy_raw.strip()

            # nissy output a solution
            if not nissy_raw.isspace():
                nissy_moves = nissy_raw

                # combined moves
                combined_moves = " ".join([
                    st.session_state.user.moves,
                    nissy_moves
                ])
                combined_moves = execute_nissy(f"unniss {combined_moves}")
                combined_moves = execute_nissy(f"cleanup {combined_moves}")

                # length of moves
                m_len = count_length(st.session_state.user.moves)
                n_len = count_length(nissy_moves)
                com_len = count_length(combined_moves)
                diff = m_len + n_len - com_len

                if diff:
                    comment = f" // {goal} ({n_len}-{diff}/{com_len})"
                elif m_len == 0:
                    comment = f" // {goal} ({n_len})"
                else:
                    comment = f" // {goal} ({n_len}/{com_len})"

                nissy_moves += comment
            else:
                nissy_moves = f"Could not find {goal}!"

        # Write Nissy output
        st.text_input("Nissy", value=nissy_moves)


def generate_random_scramble(scramble_type: str) -> str:
    """Generate a random scramble using Nissy."""

    return execute_nissy(f"scramble {scramble_type}")


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
