import extra_streamlit_components as stx
import numpy as np
import streamlit as st
from annotated_text import annotation
from annotated_text import parameters
from annotated_text.util import get_annotated_html
from streamlit.runtime.state import SessionStateProxy

from rubiks_cube.attempt import FewestMovesAttempt
from rubiks_cube.configuration import CUBE_SIZE
from rubiks_cube.graphics import COLOR
from rubiks_cube.graphics.horisontal import plot_colored_cube_2D
from rubiks_cube.graphics.horisontal import plot_cube_state
from rubiks_cube.move.generator import MoveGenerator
from rubiks_cube.move.sequence import MoveSequence
from rubiks_cube.solver import solve_step
from rubiks_cube.state import get_rubiks_cube_state
from rubiks_cube.state.utils import invert
from rubiks_cube.tag import get_rubiks_cube_pattern
from rubiks_cube.tag.cubex import CubexCollection
from rubiks_cube.tag.cubex import get_cubexes
from rubiks_cube.utils.parsing import parse_scramble
from rubiks_cube.utils.parsing import parse_user_input

parameters.PADDING = "0.25rem 0.4rem"
parameters.SHOW_LABEL_SEPARATOR = False


def app(session: SessionStateProxy, cookie_manager: stx.CookieManager) -> None:
    """Render the main app.

    Args:
        session (SessionStateProxy): Session state proxy.
        cookie_manager (stx.CookieManager): Cookie manager.
    """

    _ = cookie_manager.get_all()

    st.subheader("Rubiks Cube App")

    scramble_input = st.text_input(
        label="Scramble",
        value=cookie_manager.get("scramble_input"),
        placeholder="R' U' F ...",
    )
    if scramble_input is not None:
        session["scramble"] = parse_scramble(scramble_input)
        cookie_manager.set(cookie="scramble_input", val=scramble_input, key="scramble_input")

    scramble_state = get_rubiks_cube_state(sequence=session["scramble"])

    if st.toggle(label="Invert", key="invert_scramble", value=False):
        fig_scramble_state = invert(scramble_state)
    else:
        fig_scramble_state = scramble_state

    fig = plot_cube_state(permutation=fig_scramble_state)
    st.pyplot(fig, use_container_width=False)

    user_input = st.text_area(
        label="Moves",
        value=cookie_manager.get("user_input"),
        placeholder="Moves  // Comment\n...",
        height=200,
    )
    if user_input is not None:
        session["user"] = parse_user_input(user_input)
        cookie_manager.set(cookie="user_input", val=user_input, key="user_input")

    user_state = get_rubiks_cube_state(
        sequence=session["user"],
        initial_permutation=scramble_state,
    )

    if st.toggle(label="Invert", key="invert_user", value=False):
        fig_user_state = invert(user_state)
    else:
        fig_user_state = user_state
    fig_user = plot_cube_state(permutation=fig_user_state)
    st.pyplot(fig_user, use_container_width=False)

    attempt = FewestMovesAttempt.from_string(
        scramble_input=cookie_manager.get("scramble_input") or "",
        attempt_input=cookie_manager.get("user_input") or "",
    )
    attempt.compile()
    st.code(str(attempt), language=None)


def solver(session: SessionStateProxy, cookie_manager: stx.CookieManager) -> None:
    """Render the solver.

    Args:
        session (SessionStateProxy): Session state proxy.
        cookie_manager (stx.CookieManager): Cookie manager.
    """

    _ = cookie_manager.get_all()

    st.subheader("Rubiks Cube Solver")

    scramble_input = st.text_input(
        label="Scramble",
        value=cookie_manager.get("scramble_input"),
        placeholder="R' U' F ...",
    )
    if scramble_input is not None:
        session["scramble"] = parse_scramble(scramble_input)
        cookie_manager.set(cookie="scramble_input", val=scramble_input, key="scramble_input")

    scramble_state = get_rubiks_cube_state(sequence=session["scramble"])

    if st.toggle(label="Invert", key="invert_scramble", value=False):
        fig_scramble_state = invert(scramble_state)
    else:
        fig_scramble_state = scramble_state
    fig = plot_cube_state(permutation=fig_scramble_state)
    st.pyplot(fig, use_container_width=False)

    user_input = st.text_area(
        label="Moves",
        value=cookie_manager.get("user_input"),
        placeholder="Moves  // Comment\n...",
        height=200,
    )
    if user_input is not None:
        session["user"] = parse_user_input(user_input)
        cookie_manager.set(cookie="user_input", val=user_input, key="user_input")

    user_state = get_rubiks_cube_state(
        sequence=session["user"],
        initial_permutation=scramble_state,
    )

    if st.toggle(label="Invert", key="invert_user", value=False):
        fig_user_state = invert(user_state)
    else:
        fig_user_state = user_state
    fig_user = plot_cube_state(permutation=fig_user_state)
    st.pyplot(fig_user, use_container_width=False)

    cubexes = get_cubexes(cube_size=CUBE_SIZE)
    options = [name for name, cubex in cubexes.items() if len(cubex) == 1]

    st.subheader("Settings")
    cols = st.columns([1, 1])
    with cols[0]:
        tag = st.selectbox(
            label="Step",
            options=options,
            key="step",
        )
        n_solutions = st.number_input(
            label="Solutions",
            value=1,
            min_value=1,
            max_value=20,
            key="n_solutions",
        )
        search_strategy = st.selectbox(
            label="Search strategy",
            options=["Normal", "Inverse"],
            key="search_strat",
            label_visibility="collapsed",
        )
    with cols[1]:
        generator = st.text_input(
            label="Generator",
            value="<L, R, F, B, U, D>",
            key="generator",
        )
        max_search_depth = st.number_input(
            label="Max Depth",
            value=8,
            min_value=1,
            max_value=20,
            key="max_depth",
        )
        solve_button = st.button("Solve", type="primary", use_container_width=True)

    if solve_button and tag is not None:
        with st.spinner("Finding solutions.."):
            solutions = solve_step(
                sequence=session["scramble"] + session["user"],
                generator=MoveGenerator(generator),
                tag=tag,
                max_search_depth=int(max_search_depth),
                n_solutions=int(n_solutions),
                search_inverse=(search_strategy == "Inverse"),
            )
        if solutions is not None:
            if len(solutions) == 0:
                st.write("Cube is already solved!")
            else:
                st.write(
                    f"Found {len(solutions)}/{n_solutions} solution{'s' * (len(solutions) > 1)}:"
                )
                for solution in solutions:
                    st.markdown(
                        get_annotated_html(annotation(f"{solution}", "", background="#E6D8FD")),
                        unsafe_allow_html=True,
                    )
        else:
            st.write("Found no solutions!")


def pattern(session: SessionStateProxy, cookie_manager: stx.CookieManager) -> None:
    """Render the pattern page.

    Args:
        session (SessionStateProxy): Session state proxy.
        cookie_manager (stx.CookieManager): Cookie manager.
    """

    st.header("Patterns")

    cols = st.columns([1, 1])
    with cols[0]:
        cube_size = st.number_input(
            label="Cube size",
            value=3,
            min_value=2,
            max_value=10,
            key="size",
        )
        sequence = st.text_input(
            label="Mask of solved after sequence",
            value="",
            key="mask",
        )
    with cols[1]:
        generator = st.text_input(
            label="Generator",
            value="<L, R, F, B, U, D>",
            key="generator",
        )
        pieces = st.multiselect(
            label="Pieces",
            options=["corner", "edge", "center"],
            key="pieces",
        )
        create_pattern = st.button("Create Pattern", type="primary", use_container_width=True)

    if create_pattern:
        mask_sequence = MoveSequence(sequence) if sequence.strip() != "" else None

        cubex = CubexCollection.from_settings(
            mask_sequence=mask_sequence,
            generator=MoveGenerator(generator),
            pieces=pieces,
            cube_size=cube_size,
        )

        st.write(cubex)
        pattern = cubex.matchable_patterns[0]
        color_map = {
            0: COLOR["gray"],
            1: COLOR["white"],
            2: COLOR["green"],
            3: COLOR["red"],
            4: COLOR["blue"],
            5: COLOR["orange"],
            6: COLOR["yellow"],
            7: COLOR["cyan"],
            8: COLOR["lime"],
            9: COLOR["purple"],
            10: COLOR["pink"],
            11: COLOR["beige"],
            12: COLOR["brown"],
            13: COLOR["indigo"],
            14: COLOR["tan"],
            15: COLOR["steelblue"],
            16: COLOR["olive"],
        }
        colored_cube = np.array([color_map.get(i, None) for i in pattern])
        st.pyplot(plot_colored_cube_2D(colored_cube), use_container_width=False)


def docs(session: SessionStateProxy, cookie_manager: stx.CookieManager) -> None:
    """Render the documentation.

    Args:
        session (SessionStateProxy): Session state proxy.
        cookie_manager (stx.CookieManager): Cookie manager.
    """

    st.header("Docs")
    st.markdown("This is where the documentation should go!")

    st.markdown("## Example")

    import streamlit.components.v1 as components
    from pyvis.network import Network

    from rubiks_cube.configuration import COLOR_SCHEME
    from rubiks_cube.configuration.type_definitions import CubeMask
    from rubiks_cube.configuration.type_definitions import CubePermutation
    from rubiks_cube.graphics import get_colored_rubiks_cube
    from rubiks_cube.move.algorithm import MoveAlgorithm
    from rubiks_cube.solver.actions import get_action_space
    from rubiks_cube.solver.optimizers import IndexOptimizer
    from rubiks_cube.state.utils import infer_cube_size

    def display_actions(actions: dict[str, CubePermutation], mask: CubeMask) -> None:
        """Create a visual representation of the action space.

        Args:
            actions (dict[str, CubePermutation]): Cube actions.
        """
        net = Network(height="600px", width="100%", directed=True, bgcolor="#FFFFFF")
        cube_state = get_colored_rubiks_cube(cube_size=infer_cube_size(mask))

        for idx, face in enumerate(cube_state[mask]):
            net.add_node(idx, label=f"{idx}", shape="dot", color=COLOR_SCHEME[face])

        for action, permutation in actions.items():
            for i, j in enumerate(permutation):
                net.add_edge(i, int(j), label=action, color="#222222")

        html_str = net.generate_html()
        components.html(html_str, height=750)

    actions = get_action_space(
        algorithms=[
            MoveAlgorithm("Ua", "M2 U M U2 M' U M2"),
            MoveAlgorithm("Ub", "M2 U' M U2 M' U' M2"),
        ],
        cube_size=3,
    )
    pattern = get_rubiks_cube_pattern(tag="solved", cube_size=3)

    optimizer = IndexOptimizer(cube_size=3)
    actions, pattern = optimizer.fit_transform(actions=actions, pattern=pattern)

    display_actions(actions=actions, mask=optimizer.mask)
