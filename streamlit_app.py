import pickle
import streamlit as st
import subprocess

from utils import plot_cube_state, apply_turns

st.set_page_config(
    page_title="Fewest Moves Solver",
    page_icon="data/favicon.png",
    layout="centered",
)


default_values = {
    "initialized": False,
    "cube_state": None,
    "cube_state_solved": None,
    "scramble": "",
    "draw_scramble": True,
    "invert_scramble": False,
    "unniss_scramble": False,
    "cleanup_scramble": False,
    "solution": "",
    "draw_solution": True,
    "invert_solution": False,
    "unniss_solution": True,
    "cleanup_solution": True,
    "find_eo": False,
    "find_dr": False,
    "find_htr": False,
    "find_rest": False,
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
    elif any(c not in "UDFBLRudfblrMESxyzw2' ()" for c in scramble):
        return False
    return scramble


# TODO: Clean up this function
def count_length(sequence, count_rotations=False, metric="HTM"):
    """Count the length of a sequence."""
    sequence = sequence.replace("(", "").replace(")", "").strip()

    sum_rotations = sum(1 for char in sequence if char in "xyz")
    sum_slices = sum(1 for char in sequence if char in "MES")
    sum_double_moves = sum(1 for char in sequence if char in "2")
    sum_moves = len(sequence.split())

    if count_rotations:
        if metric == "HTM":
            return sum_moves + sum_slices
        elif metric == "STM":
            return sum_moves
        elif metric == "QTM":
            return sum_moves + sum_double_moves
        else:
            raise ValueError(f"Invalid metric: {metric}")
    else:
        if metric == "HTM":
            return sum_moves + sum_slices - sum_rotations
        elif metric == "STM":
            return sum_moves - sum_rotations
        elif metric == "QTM":
            return sum_moves + sum_double_moves - sum_rotations
        else:
            raise ValueError(f"Invalid metric: {metric}")


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


def render_nissy_commands():  # TODO: Possibly remove this
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


def render_scramble_settings_bar():
    """Render the settings bar."""
    col1, col2, col3, col4 = st.columns(4)
    st.session_state.draw_scramble = col1.toggle(
        label="Draw scramble",
        value=st.session_state.draw_scramble,
    )
    if False:  # TODO: Remove this
        st.session_state.invert_scramble = col2.toggle(
            label="Invert",
            value=st.session_state.invert_scramble,
        )
        st.session_state.unniss_scramble = col3.toggle(
            label="Unniss",
            value=st.session_state.unniss_scramble,
        )
        st.session_state.cleanup_scramble = col4.toggle(
            label="Cleanup",
            value=st.session_state.cleanup_scramble,
        )


def render_solution_settings_bar():
    """Render the settings bar."""
    col1, col2, col3, col4 = st.columns(4)
    st.session_state.draw_solution = col1.toggle(
        label="Draw solution",
        value=st.session_state.draw_solution,
    )
    st.session_state.unniss_solution = col2.toggle(
        label="Unniss",
        value=st.session_state.unniss_solution,
    )
    st.session_state.cleanup_solution = col3.toggle(
        label="Cleanup",
        value=st.session_state.cleanup_solution,
    )
    st.session_state.invert_solution = col4.toggle(
        label="Invert",
        value=st.session_state.invert_solution,
    )


def render_nissy_bar():
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
        label="Find solution"
    )
    return find_eo, find_dr, find_htr, find_rest


def render_blocky_bar():
    """Render the action bar."""
    col1, col2, col3, col4 = st.columns(4)
    find_222 = col1.button(
        label="Find 2x2x2"
    )
    find_223 = col2.button(
        label="Find 2x2x3"
    )
    find_f2lm1 = col3.button(
        label="Find F2L-1"
    )
    find_ll = col4.button(
        label="Find LL"
    )
    return find_222, find_223, find_f2lm1, find_ll


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
    raw_scramble = st.text_input("Scramble", placeholder="R' U' F ...")

    if scramble := is_valid(raw_scramble):
        render_scramble_settings_bar()

        if False:
            modified = False
            if st.session_state.invert_scramble:
                modified = True
                scramble = execute_nissy(f"invert {scramble}")
            if st.session_state.unniss_scramble:
                modified = True
                scramble = execute_nissy(f"unniss {scramble}")
            if st.session_state.cleanup_scramble:
                modified = True
                scramble = execute_nissy(f"cleanup {scramble}")
            if modified:
                st.text_input("Modified scramble", value=scramble)

        # Draw scramble
        if st.session_state.draw_scramble:
            st.session_state.cube_state = apply_turns(scramble)
            figure = plot_cube_state(st.session_state.cube_state)
            st.pyplot(figure, use_container_width=True)

        # Solution
        solution = st.text_area(
            "Solution / Skeleton",
            placeholder="Moves // Comment 1\nMore moves // Comment 2\n..."
        )

        # Solve scramble with solution
        sequences = []
        if solution == "":
            st.info("Enter a solution to get started or use the tools!")
        else:
            for line in solution.strip().split("\n"):
                sequence = line.split("//")[0]
                if sequence := is_valid(sequence):
                    sequences.append(sequence)
                elif sequence == "":
                    continue
                else:
                    st.warning("Invalid sequence entered!")
                    break
            solution = " ".join(sequences)

        if solution := is_valid(solution):
            render_solution_settings_bar()
            # Options
            if st.session_state.invert_solution:
                solution = execute_nissy(f"invert {solution}")
            if st.session_state.unniss_solution:
                solution = execute_nissy(f"unniss {solution}")
            if st.session_state.cleanup_solution:
                solution = execute_nissy(f"cleanup {solution}")
            st.text_input(
                "Collapsed solution",
                value=solution + f" // ({count_length(solution)})"
            )

            st.session_state.solution = solution

            # Draw solution
            if st.session_state.draw_solution:
                st.session_state.cube_state_solved = apply_turns(
                    sequence=st.session_state.solution,
                    cube_state=st.session_state.cube_state
                )
                figure_solution = plot_cube_state(
                    st.session_state.cube_state_solved
                )
                st.pyplot(figure_solution, use_container_width=True)

        elif solution == "":
            st.info("Enter a solution to get started!")

        # Solve scramble with Nissy
        st.subheader("Use Nissy")  # TODO: Add solve functionality
        find_eo, find_dr, find_htr, find_rest = render_nissy_bar()

        # Solve scramble with Blocky
        st.subheader("Use Blocky")  # TODO: Add solve functionality
        find_222, find_223, find_f2lm1, find_ll = render_blocky_bar()

        # Use Insertion Finder
        st.subheader("Insertion Finder")
        find_insertions = st.button(
            label="Find insertions"
        )

    elif raw_scramble == "":
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
