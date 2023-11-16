import streamlit as st
from tools.nissy import Nissy, execute_nissy
from utils.rubiks_cube import (
    validate_sequence,
    split_sequence,
    is_valid_rubiks_cube_moves,
    Sequence
)
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
    "scramble": Sequence(),
    "user_moves": Sequence(),
    "tool_moves": Sequence(),
    "use_premoves": True,
    "invert": False,
    "unniss": True,
    "cleanup": True,
}

for key, default in default_values.items():
    if key not in st.session_state:
        setattr(st.session_state, key, default)


def render_user_settings():
    """Render the settings bar."""

    col1, col2, _, _ = st.columns(4)
    st.session_state.use_premoves = col1.toggle(
        label="Use premoves",
        value=st.session_state.use_premoves,
    )
    st.session_state.invert = col2.toggle(
        label="Invert",
        value=st.session_state.invert,
    )


def render_main_page():
    """Render the main page."""

    st.title("Fewest Moves Solver")
    scramble = st.text_input("Scramble", placeholder="R' U' F ...")

    # Scramble
    if scramble == "":
        st.info("Enter a scramble to get started!")
    elif scramble_comment := validate_sequence(scramble):
        st.session_state.scramble, _ = scramble_comment
        fig = plot_cube_state(st.session_state.scramble)
        st.pyplot(fig, use_container_width=True)

        # User moves
        user_input = st.text_area(
            "Moves",
            placeholder="Moves // Comment 1\nMore moves // Comment 2\n..."
        )
        user_moves = Sequence()
        if user_input == "":
            st.info("Enter some moves to get started or use the tools!")
        else:
            for raw_line in user_input.strip().split("\n"):
                if line_comment := validate_sequence(raw_line):
                    line, _ = line_comment
                    user_moves += line
                elif raw_line.strip() == "":
                    continue
                else:
                    st.warning("Invalid moves entered!")
                    break

            if is_valid_rubiks_cube_moves(user_moves.moves):

                st.session_state.user_moves = Sequence(
                    execute_nissy(f"cleanup {user_moves.moves}")
                )
                normal_moves, inverse_moves = split_sequence(
                    st.session_state.user_moves
                )
                pre_moves = Sequence(
                    inverse_moves.moves.replace("(", "").replace(")", "")
                )
                pre_moves = ~ pre_moves

                if st.session_state.unniss:
                    st.session_state.user_moves = Sequence(
                        execute_nissy(f"unniss {st.session_state.user_moves}")
                    )
                out_string = st.session_state.user_moves.moves
                out_string += f" // ({len(st.session_state.user_moves)})"

                text = "Draft"  # / Skeleton / Solution
                st.text_input(text, value=out_string)

                render_user_settings()

                if st.session_state.use_premoves:
                    full_sequence = pre_moves + \
                        st.session_state.scramble + \
                        normal_moves
                else:
                    full_sequence = st.session_state.scramble + \
                        st.session_state.user_moves

                full_sequence = Sequence(
                    execute_nissy(f"unniss {full_sequence}")
                )

                if st.session_state.invert:
                    full_sequence = ~ full_sequence

                # Draw draft
                fig_user = plot_cube_state(full_sequence)
                st.pyplot(fig_user, use_container_width=True)

            elif user_moves.moves:
                st.warning("Invalid moves entered!")

        # Render tools
        for tool in tools:
            st.write("")
            st.subheader(tool)
            tool.render()
    else:
        st.warning("Invalid scramble entered!")


if __name__ == "__main__":
    render_main_page()
