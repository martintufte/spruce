import streamlit as st

from utils.rubiks_cube import (
    split_into_moves_comment,
    split_normal_inverse,
    is_valid_symbols,
    is_valid_moves,
    Sequence
)
from utils.plotting import plot_cube_state
from tools.nissy import Nissy, execute_nissy

st.set_page_config(
    page_title="Fewest Moves Solver",
    page_icon="data/favicon.png",
    layout="centered",
)

tools = [
    Nissy(),
]

default_values = {
    "scramble": Sequence(),
    "user": Sequence(),
    "tool": Sequence(),
    "premoves": True,
    "invert": False,
}

for key, default in default_values.items():
    if key not in st.session_state:
        setattr(st.session_state, key, default)


def render_user_settings():
    """Render the settings bar."""

    col1, col2, _, _ = st.columns(4)
    st.session_state.premoves = col1.toggle(
        label="Use premoves",
        value=st.session_state.premoves,
    )
    st.session_state.invert = col2.toggle(
        label="Invert",
        value=st.session_state.invert,
    )


def render_main_page():
    """Render the main page."""

    st.title("Fewest Moves Solver")

    # Scramble
    scramble_input = st.text_input("Scramble", placeholder="R' U' F ...")
    scramble, _ = split_into_moves_comment(scramble_input)

    # Check if scramble is valid
    if scramble.strip() == "":
        st.session_state.scramble = Sequence()
        st.info("Enter a scramble to get started!")
    elif not is_valid_symbols(scramble):
        st.error("Invalid symbols entered!")
    elif not is_valid_moves(scramble):
        st.error("Invalid moves entered!")
    else:
        st.session_state.scramble = Sequence(scramble)

        # Draw scramble
        fig = plot_cube_state(st.session_state.scramble)
        st.pyplot(fig, use_container_width=True)

        # User moves
        user_input = st.text_area("Moves", placeholder="Moves // Comment\n...")
        user = Sequence()
        user_comments = []

        if user_input.strip() == "":
            st.session_state.user = Sequence()
            st.info("Enter some moves to get started or use the tools!")
        else:
            for i, line_input in enumerate(user_input.split("\n")):
                line, comment = split_into_moves_comment(line_input)
                user_comments.append(comment)
                if line_input.strip() == "":
                    continue
                elif not is_valid_symbols(line):
                    st.warning("Invalid symbols entered at line " + str(i+1))
                elif not is_valid_moves(line):
                    st.warning("Invalid moves entered!")
                    break
                else:
                    user += Sequence(line)

            # Check if it is valid
            if not is_valid_moves(user.moves):
                st.warning("Invalid moves entered!")
            else:
                st.session_state.user = Sequence(
                    execute_nissy(f"cleanup {user.moves}")
                )
                normal_moves, inverse_moves = split_normal_inverse(
                    st.session_state.user
                )
                pre_moves = Sequence(
                    inverse_moves.moves.replace("(", "").replace(")", "")
                )
                pre_moves = ~ pre_moves

                out = Sequence(st.session_state.user.moves)
                out.moves = execute_nissy(f"unniss {out.moves}")
                out.moves = execute_nissy(f"cleanup {out.moves}")

                out_comment = "?"  # Blind trace?
                out_string = out.moves + f" // {out_comment} ({len(out)})"
                st.text_input("Draft", value=out_string)

                render_user_settings()

                if st.session_state.premoves:
                    full_sequence = pre_moves + \
                        st.session_state.scramble + \
                        normal_moves
                else:
                    full_sequence = st.session_state.scramble + \
                        st.session_state.user

                full_sequence = Sequence(
                    execute_nissy(f"unniss {full_sequence}")
                )
                if st.session_state.invert:
                    full_sequence = ~ full_sequence

                # Draw draft
                fig_user = plot_cube_state(full_sequence)
                st.pyplot(fig_user, use_container_width=True)

        # Tools
        for tool in tools:
            st.write("")
            st.subheader(tool)
            tool.render()


if __name__ == "__main__":
    render_main_page()
