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
    "scramble": "",
    "moves": "",
    "nissy": "",
    "insertion_finder": "",
    "cube_state_scrambled": None,
    "cube_state_moved": None,
    "draw_scramble": True,
    "debug_scramble": False,
    "draw_moved": True,
    "unniss_moved": True,
    "cleanup_moved": True,
    "invert_moved": False,
    "find_eo": False,
    "find_dr": False,
    "find_htr": False,
    "find_rest": False,
    "find_insertions": False,
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


def count_length(sequence, count_rotations=False, metric="HTM"):
    """Count the length of a sequence."""
    sequence = sequence.replace("(", "").replace(")", "").strip()

    sum_rotations = sum(1 for char in sequence if char in "xyz")
    sum_slices = sum(1 for char in sequence if char in "MES")
    sum_double_moves = sum(1 for char in sequence if char in "2")
    sum_moves = len(sequence.split())

    if not count_rotations:
        sum_moves -= sum_rotations

    if metric == "HTM":
        return sum_moves + sum_slices
    elif metric == "STM":
        return sum_moves
    elif metric == "QTM":
        return sum_moves + sum_double_moves 
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


def render_scramble_settings():
    """Render the settings bar."""
    col1, col2, col3, col4 = st.columns(4)
    st.session_state.draw_scramble = col1.toggle(
        label="Draw scramble",
        value=st.session_state.draw_scramble,
    )
    st.session_state.debug_scramble = col2.toggle(
        label="Debug",
        value=st.session_state.debug_scramble,
    )


def render_moved_settings():
    """Render the settings bar."""
    col1, col2, col3, col4 = st.columns(4)
    st.session_state.draw_moved = col1.toggle(
        label="Draw",
        value=st.session_state.draw_moved,
    )
    st.session_state.unniss_moved = col2.toggle(
        label="Unniss",
        value=st.session_state.unniss_moved,
    )
    st.session_state.cleanup_moved = col3.toggle(
        label="Cleanup",
        value=st.session_state.cleanup_moved,
    )
    st.session_state.invert_moved = col4.toggle(
        label="Invert",
        value=st.session_state.invert_moved,
    )


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
        label="Find solution"
    )
    return find_eo, find_dr, find_htr, find_rest


def render_insertion_finder_buttons():
    """Render the action bar."""
    col1, col2, col3, col4 = st.columns(4)
    find_222 = col1.button(
        label="Insert corners"
    )
    find_223 = col2.button(
        label="Insert edges"
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

    # Raw scramble
    raw_scramble = st.text_input("Scramble", placeholder="R' U' F ...")

    if scramble := is_valid(raw_scramble):
        render_scramble_settings()

        # Draw scramble
        if st.session_state.draw_scramble:
            st.session_state.cube_state = apply_turns(scramble)
            figure = plot_cube_state(st.session_state.cube_state)
            st.pyplot(figure, use_container_width=True)

        # Debug scramble  # TODO_ Add debug functionality
        if st.session_state.debug_scramble:
            text = f"Scramble length: {count_length(scramble)}  \n"
            text += "EO F/B: 4  \n"
            text += "EO R/L: 6  \n"
            text += "EO U/D: 8  \n"
            text += "Blind trace: 6c2c 3e7e2e  \n"
            st.info(text, icon="ℹ️")
        
        # Save scramble
        st.session_state.scramble = scramble

        # Raw moves
        raw_moves = st.text_area(
            "Moves",
            placeholder="Moves // Comment 1\nMore moves // Comment 2\n..."
        )

        # Solve scramble with moves
        all_moves = []
        if raw_moves == "":
            st.info("Enter some moves to get started or use the tools!")
            st.session_state.moves = ""
        else:
            for line in raw_moves.strip().split("\n"):
                line_moves = line.split("//")[0]
                if line_moves := is_valid(line_moves):
                    all_moves.append(line_moves)
                elif line_moves == "":
                    continue
                else:
                    st.warning("Invalid moves entered!")
                    break
            raw_moves = " ".join(all_moves)

        if moves := is_valid(raw_moves):
            render_moved_settings()

            st.session_state.moves = execute_nissy(f"unniss {moves}")

            scramble_moves = " ".join([
                st.session_state.scramble,
                st.session_state.moves
            ])

            if st.session_state.unniss_moved:
                moves = st.session_state.moves
            if st.session_state.cleanup_moved:
                moves = execute_nissy(f"cleanup {moves}")

            if st.session_state.invert_moved:
                scramble_moves = execute_nissy(f"invert {scramble_moves}")

            # TODO: Write "skeleton" if moves is close to solved
            # TODO: Write "solution" if cube is solved
            st.text_input(
                "Skeleton",
                value=moves + f" // ({count_length(moves)})"
            )

            st.session_state.moves = moves
            st.session_state.cube_state_moved = apply_turns(
                sequence=scramble_moves
            )

            # Draw solution
            if st.session_state.draw_moved:

                figure_solution = plot_cube_state(
                    st.session_state.cube_state_moved
                )
                st.pyplot(figure_solution, use_container_width=True)

        # Use Nissy
        st.subheader("Nissy")  # TODO: Add solve functionality
        find_eo, find_dr, find_htr, find_rest = render_nissy_buttons()

        if find_eo:
            with st.spinner("Finding EO..."):
                sequence = " ".join([st.session_state.scramble, st.session_state.moves])
                st.session_state.nissy = execute_nissy(f"solve eo {sequence}")
                # format output
                if st.session_state.nissy.find("(") != -1:
                    idx = st.session_state.nissy.find("(")
                    st.session_state.nissy = st.session_state.nissy[:idx] + \
                        "// E0 " + st.session_state.nissy[idx:]
        if find_dr:
            with st.spinner("Finding DR..."):
                sequence = " ".join([st.session_state.scramble, st.session_state.moves])
                st.session_state.nissy = execute_nissy(f"solve dr {sequence}")
                # format output
                if st.session_state.nissy.find("(") != -1:
                    idx = st.session_state.nissy.find("(")
                    st.session_state.nissy = st.session_state.nissy[:idx] + \
                        "// DR " + st.session_state.nissy[idx:]
        if find_htr:
            with st.spinner("Finding HTR..."):
                sequence = " ".join([st.session_state.scramble, st.session_state.moves])
                st.session_state.nissy = execute_nissy(f"solve htr {sequence}")
                # format output
                if st.session_state.nissy.find("(") != -1:
                    idx = st.session_state.nissy.find("(")
                    st.session_state.nissy = st.session_state.nissy[:idx] + \
                        "// HTR " + st.session_state.nissy[idx:]
        if find_rest:
            with st.spinner("Finishing..."):
                sequence = " ".join([st.session_state.scramble, st.session_state.moves])
                st.session_state.nissy = execute_nissy(f"solve htrfin {sequence}")
                # format output
                if st.session_state.nissy.find("(") != -1:
                    idx = st.session_state.nissy.find("(")
                    st.session_state.nissy = st.session_state.nissy[:idx] + \
                        "// Finish " + st.session_state.nissy[idx:]

        # Write Nissy output
        st.text_input("Nissy", value=st.session_state.nissy)

        # Use Insertion Finder
        st.subheader("Insertion Finder")
        find_222, find_223, find_f2lm1, find_ll = render_insertion_finder_buttons()

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
