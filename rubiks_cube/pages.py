import streamlit as st
import extra_streamlit_components as stx
from annotated_text.util import get_annotated_html
from annotated_text import parameters, annotation
from streamlit.runtime.state import SessionStateProxy
from rubiks_cube.fewest_moves import FewestMovesAttempt
from rubiks_cube.graphics import plot_cubex
from rubiks_cube.graphics import plot_cube_state
from rubiks_cube.state import get_rubiks_cube_state
from rubiks_cube.utils.parsing import parse_user_input
from rubiks_cube.utils.parsing import parse_scramble
from rubiks_cube.state.tag.patterns import get_cubexes
from rubiks_cube.state.permutation import invert

parameters.PADDING = "0.25rem 0.4rem"
parameters.SHOW_LABEL_SEPARATOR = False


def app(
    session: SessionStateProxy,
    cookie_manager: stx.CookieManager,
) -> None:
    """Render the main app."""

    # Update cookies to avoid visual bugs with input text areas
    _ = cookie_manager.get_all()

    st.subheader("Rubiks Cube Solver")

    scramble_input = st.text_input(
        label="Scramble",
        value=cookie_manager.get("scramble_input"),
        placeholder="R' U' F ..."
    )
    if scramble_input is not None:
        session.scramble = parse_scramble(scramble_input)
        cookie_manager.set(
            cookie="scramble_input",
            val=scramble_input,
            key="scramble_input"
        )

    scramble_state = get_rubiks_cube_state(sequence=session.scramble)

    if st.toggle(label="Invert", key="invert_scramble", value=False):
        fig_scramble_state = invert(scramble_state)
    else:
        fig_scramble_state = scramble_state
    fig = plot_cube_state(fig_scramble_state)
    st.pyplot(fig, use_container_width=False)

    # User input handling:
    user_input = st.text_area(
        label="Moves",
        value=cookie_manager.get("user_input"),
        placeholder="Moves  // Comment\n...",
        height=200
    )
    if user_input is not None:
        session.user = parse_user_input(user_input)
        cookie_manager.set(
            cookie="user_input",
            val=user_input,
            key="user_input"
        )

    user_state = get_rubiks_cube_state(
        sequence=session.user,
        initial_state=scramble_state,
    )

    if st.toggle(label="Invert", key="invert_user", value=False):
        fig_user_state = invert(user_state)
    else:
        fig_user_state = user_state
    fig_user = plot_cube_state(fig_user_state)
    st.pyplot(fig_user, use_container_width=False)

    attempt = FewestMovesAttempt.from_string(
        cookie_manager.get("scramble_input") or "",
        cookie_manager.get("user_input") or "",
    )
    attempt.compile()
    st.code(str(attempt), language=None)

    if False:
        st.markdown("**Scramble**: R' U' F L U B' D' L F2 U2 D' B U R2 D F2 R2 F2 L2 D' F2 D2 R' U' F")  # noqa: E501

        for step, tag, subset, moves, cancels, total in attempt:
            if cancels > 0:
                counter_str = f" ({moves}-{cancels}/{total})"
            else:
                counter_str = f" ({moves}/{total})"

            # Tag colors purple
            tag_background_color = {
                "eo": "#FFEDD3",
                "drm": "#FFDBDB",
                "dr": "#E6D8FD",
                "htr": "#CEE6FF",
                "solved": "#D3F3DD",
            }

            st.markdown(
                f"{str(step)}  ".replace(" ", "&nbsp;") +
                get_annotated_html(
                    annotation(tag, counter_str, background=tag_background_color[tag])  # noqa: E501
                ),
                unsafe_allow_html=True,
            )


def patterns(
    session: SessionStateProxy,
    cookie_manager: stx.CookieManager,
) -> None:

    scramble_state = get_rubiks_cube_state(sequence=session.scramble)

    user_state = get_rubiks_cube_state(
        sequence=session.user,
        initial_state=scramble_state,
    )

    st.subheader("Patterns")
    cubexes = get_cubexes()
    tag = st.selectbox(
        label=" ",
        options=cubexes.keys(),
        label_visibility="collapsed"
    )
    if tag is not None:
        cubex = cubexes[tag]
        st.write(tag, len(cubex), cubex.match(user_state))
        for pattern in cubex.patterns:
            fig_pattern = plot_cubex(pattern)
            st.pyplot(fig_pattern, use_container_width=True)


documentation = """

```py
seq = MoveSequence("R' U' F")
```

### Example table

| Pattern | Description |
| ----------- | ----------- |
| eo | Edge orientation |
| dr | Domino reduction |

Created my Martin Gudahl Tufte
"""


def docs(
    session: SessionStateProxy,
    cookie_manager: stx.CookieManager,
) -> None:
    """This is where the documentation should go!"""

    st.header("Docs")
    # st.subheader("")
    # st.markdown(documentation)

    if False:
        import altair as alt
        import pandas as pd

        # Sample data
        data = pd.DataFrame({
            'x': [1, 2, 3],
            'y': [4, 5, 6]
        })

        # Create a chart
        chart = alt.Chart(data).mark_line().encode(
            x='x',
            y='y'
        ).properties(
            width=300,
            height=200
        )

        # Display the chart in Streamlit
        st.altair_chart(chart)

        import plotly.graph_objects as go

        shape = {
            'type': 'rect',
            'x0': 0, 'y0': 0,
            'x1': 1, 'y1': 1,
            'line': {
                'color': 'rgba(128, 0, 128, 1)',
                'width': 2,
            },
            'fillcolor': 'rgba(128, 0, 128, 0.5)',
        }

        # Create the figure
        fig = go.Figure()

        # Add the rectangle to the figure
        fig.add_shape(shape)

        # Update the layout to remove axes
        fig.update_layout(
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            width=400,
            height=400,
            margin=dict(r=10, l=10, b=10, t=10)
        )

        # Display the plot in Streamlit without the mode bar
        st.plotly_chart(fig, use_container_width=True, config={
            'displayModeBar': False,
            'staticPlot': True
        })
