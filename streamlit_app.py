import pickle
import streamlit as st
import subprocess
import matplotlib.pyplot as plt

st.set_page_config(
    page_title="Fewest Moves Solver",
    page_icon="data/favicon.png",
    layout="centered",
)


default_values = {
    "initialized": False,
    "scramble": "",
    "draw_scramble": True,
    "invert": False,
    "unniss": False,
    "cleanup": False,
}

for key, default in default_values.items():
    if key not in st.session_state:
        setattr(st.session_state, key, default)

if not st.session_state.initialized:
    st.session_state["initialized"] = True
else:
    print("Initialized state:", st.session_state.initialized)


def reset_session():
    """Reset the session state."""
    st.session_state["initialized"] = False
    print("Session reset!")


def save_app_state(path="data/processed/saved_app_state.pkl"):
    """Save session state to disk."""
    with open(path, "wb") as f:
        pickle.dump(st.session_state.agent_state, f)


def is_valid(scramble):
    """Check if a scramble is valid."""
    # remove leading and trailing whitespace
    scramble = scramble.strip()
    # remove double spaces
    scramble = " ".join(scramble.split())
    # no scramble
    if len(scramble) == 0:
        return False
    # check for invalid characters
    elif any(c not in "UDFBLRudfblrMESxyz2' ()" for c in scramble):
        return False
    return scramble


def execute_nissy_command(command):
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


def render_nissy_commands():
    # Nissy commands
    with st.expander("Nissy commands", expanded=False):
        st.subheader("Helper")
        st.write("""```
commands  (Lists available commands)\n
freemem  (Free large tables from RAM)\n
gen [-t N]  (Generate all tables using N threads)\n
help [COMMAND]  (Display nissy manual page of help on specific command) \n
print SCRAMBLE  (Print written description of the cube)\n
ptable [TABLE]  (Print information on pruning tables)\n
quit  (Quit nissy)\n
scramble [TYPE] [-n N]  (Get a random-position scramble)\n
steps  (List available steps)\n
twophase  (Find a solution quickly using a 2-phase method)\n
cleanup SCRAMBLE  (Rewrite a scramble using only standard moves (HTM))\n
unniss SCRAMBLE  (Rewrite a scramble without NISS)\n
version (Print NiSSy version)""")

        st.subheader("Manipulation")
        st.write("""```
invert SCRAMBLE  (Invert a scramble)\n
solve STEP [OPTIONS] SCRAMBLE  (Solve a step; see command steps for all steps)\n
twophase  (Find a solution quickly using a 2-phase method)
""")


def render_settings_bar():
    col1, col2, col3, col4 = st.columns(4)
    st.session_state.draw_scramble = col1.toggle(
        label="Draw scramble",
        value=st.session_state.draw_scramble,
    )
    st.session_state.invert = col2.toggle(
        label="Invert",
        value=st.session_state.invert,
    )
    st.session_state.unniss = col3.toggle(
        label="Unniss",
        value=st.session_state.unniss,
    )
    st.session_state.cleanup = col4.toggle(
        label="Cleanup",
        value=st.session_state.cleanup,
    )


def render_action_bar():
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
        label="Solve rest"
    )
    return find_eo, find_dr, find_htr, find_rest


def render_main_page():
    st.write(
        """
        <style>
            div[data-testid="stTickBarMin"],
            div[data-testid="stTickBarMax"] {
                display: none !important;
            }
            div.st-emotion-cache-1sghavo {
                height: 1rem;
                width: 1rem;
            }
            div[data-testid="stVerticalBlock"] div:has(div.fixed-header) {
                position: sticky;
                top: 2.875rem;

                z-index: 999;
            }
            .fixed-header {
                border-bottom: 1px solid black;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.title("Fewest Moves Solver")
    raw_input = st.text_input("Scramble", placeholder="Enter a scramble")

    render_settings_bar()

    if scramble := is_valid(raw_input):
        # Modify scramble
        modified = False
        if st.session_state.invert:
            modified = True
            scramble = execute_nissy_command(f"invert {scramble}")
        if st.session_state.unniss:
            modified = True
            scramble = execute_nissy_command(f"unniss {scramble}")
        if st.session_state.cleanup:
            modified = True
            scramble = execute_nissy_command(f"cleanup {scramble}")
        if modified:
            st.text_input("Modified scramble", value=scramble)
        # Draw scramble
        if st.session_state.draw_scramble:
            pass  # TODO: Draw scramble

        # Solve scramble
        # st.subheader("Solve")  # TODO: Add solve functionality
        # find_eo, find_dr, find_htr, find_rest = render_action_bar()

    elif raw_input == "":
        st.info("Enter a scramble to get started!")

    else:
        st.warning("Invalid scramble entered!")


def main():
    st.write(
        """
        <style>
            div[data-testid="stTickBarMin"],
            div[data-testid="stTickBarMax"] {
                display: none !important;
            }
            .css-1h0qo4c {
                height: 1.13rem;
                width: 1.13rem;
            }
            div[data-testid="stVerticalBlock"] div:has(div.fixed-header) {
                position: sticky;
                top: 2.875rem;

                z-index: 999;
            }
            .fixed-header {
                border-bottom: 1px solid black;
            }
        </style>
    """,
        unsafe_allow_html=True,
    )

    render_main_page()


if __name__ == "__main__":
    main()
