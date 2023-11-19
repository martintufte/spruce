import streamlit as st
from tools.nissy import Nissy, execute_nissy
from utils.rubiks_cube import (
    count_length,
    debug_cube_state,
    validate_sequence,
    split_sequence,
    is_valid_rubiks_cube_moves
)
from utils.permutations import is_solved
from utils.plotting import plot_cube_state

st.set_page_config(
    page_title="Fewest Moves Solver",
    page_icon="data/favicon.png",
    layout="centered",
)

tools = [
    Nissy()
]

default_values = {
    "initialized": False,
    "user_moves": "",
    "cube_state_scramble": CubeState(),
    "cube_state_user": CubeState(),
    "cube_state_tool": CubeState(),
    "use_premoves": True,
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


def render_scramble_settings():
    """Render the settings bar."""

    col1, col2, col3, col4 = st.columns(4)
    st.session_state.cube_state_scramble.draw = col1.toggle(
        label="Draw scramble",
        value=st.session_state.cube_state_scramble.draw,
    )
    st.session_state.cube_state_scramble.debug = col2.toggle(
        label="Debug",
        value=st.session_state.cube_state_scramble.debug,
    )


def render_user_settings():
    """Render the settings bar."""

    col1, col2, col3, col4 = st.columns(4)
    st.session_state.use_premoves = col1.toggle(
        label="Use premoves",
        value=st.session_state.use_premoves,
    )
    st.session_state.cube_state_user.unniss = col2.toggle(
        label="Unniss",
        value=st.session_state.cube_state_user.unniss,
    )
    st.session_state.cube_state_user.draw = col3.toggle(
        label="Draw",
        value=st.session_state.cube_state_user.draw,
    )
    st.session_state.cube_state_user.invert = col4.toggle(
        label="Invert",
        value=st.session_state.cube_state_user.invert,
    )


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

    if raw_scramble == "":
        st.info("Enter a scramble to get started!")

    elif scramble_comment := validate_sequence(raw_scramble):
        scramble, _ = scramble_comment

        # Clean the scramble and unniss
        scramble = execute_nissy(f"unniss {scramble}")

        # Set CubeState for scramble
        st.session_state.cube_state_scramble.from_sequence(scramble)

        # Render scramble settings
        render_scramble_settings()

        # Draw scramble
        if st.session_state.cube_state_scramble.draw:
            fig = plot_cube_state(
                st.session_state.cube_state_scramble.sequence
            )
            st.pyplot(fig, use_container_width=True)

        # Debug scramble
        if st.session_state.cube_state_scramble.debug:
            text = debug_cube_state(
                st.session_state.cube_state_scramble
            )
            st.info(text, icon="ℹ️")

        # Raw moves
        raw_user_moves = st.text_area(
            "Moves",
            placeholder="Moves // Comment 1\nMore moves // Comment 2\n..."
        )

        # Full sequence is scramble + user moves
        all_user_moves = []
        if raw_user_moves == "":
            st.info("Enter some moves to get started or use the tools!")

            # Update CubeState for user
            st.session_state.user_moves = ""
            st.session_state.cube_state_user.from_sequence(
                st.session_state.cube_state_scramble.sequence
            )
        else:
            for raw_line in raw_user_moves.strip().split("\n"):
                if line_comment := validate_sequence(raw_line):
                    line, _ = line_comment
                    all_user_moves.append(line)
                elif raw_line.strip() == "":
                    continue
                else:
                    st.warning("Invalid moves entered!")
                    break
            raw_user_moves = " ".join(all_user_moves)

            st.write(raw_user_moves)

            if is_valid_rubiks_cube_moves(raw_user_moves):
                render_user_settings()

                st.session_state.user_moves = execute_nissy(
                    f"cleanup {raw_user_moves}"
                )

                normal_moves, inverse_moves = split_sequence(
                    st.session_state.user_moves
                )
                pre_moves = inverse_moves.replace("(", "").replace(")", "")
                pre_moves = execute_nissy(f"invert {pre_moves}")

                if st.session_state.use_premoves:
                    full_seq = " ".join([
                        pre_moves.strip(),
                        st.session_state.cube_state_scramble.sequence.strip(),
                        normal_moves.strip()
                    ])
                else:
                    full_seq = " ".join([
                        st.session_state.cube_state_scramble.sequence.strip(),
                        st.session_state.user_moves.strip()
                    ])

                full_seq = execute_nissy(f"unniss {full_seq}")

                if st.session_state.cube_state_user.invert:
                    full_seq = execute_nissy(f"invert {full_seq}")

                if st.session_state.cube_state_user.unniss:
                    st.session_state.cube_state_user.sequence = execute_nissy(
                        f"unniss {st.session_state.user_moves}"
                    )
                out_moves = st.session_state.user_moves
                out_moves += f" // ({count_length(st.session_state.user_moves)})"
                text = "Solution" if is_solved(
                    st.session_state.cube_state_user.permutation
                ) else "Skeleton"
                st.text_input(text, value=out_moves)

                # Update CubeState for user
                st.session_state.cube_state_user.from_sequence(full_seq)

                # Draw scramble + user moves
                if st.session_state.cube_state_user.draw:
                    fig_user = plot_cube_state(
                        full_seq
                    )
                    st.pyplot(fig_user, use_container_width=True)

                # Debug scramble + user moves
                if st.session_state.cube_state_scramble.debug:
                    text = debug_cube_state(
                        st.session_state.cube_state_user
                    )
                    st.info(text, icon="ℹ️")
            elif not raw_user_moves == "":
                st.warning("Invalid moves entered!")

        # Render tools
        for tool in tools:
            st.write("")
            st.subheader(tool)
            tool.render()
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
