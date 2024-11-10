import os
from functools import partial
from typing import Any
from typing import Final

import extra_streamlit_components as stx
import streamlit as st

from rubiks_cube.configuration.logging import configure_logging
from rubiks_cube.configuration.paths import RESOURCES_DIR
from rubiks_cube.pages import autotagger
from rubiks_cube.pages import docs
from rubiks_cube.pages import pattern
from rubiks_cube.pages import solver
from rubiks_cube.parsing import parse_scramble
from rubiks_cube.parsing import parse_steps

st.set_page_config(
    page_title="Rubik's Cube Toolbox",
    page_icon=os.path.join(RESOURCES_DIR, "favicon.png"),
)


@st.fragment
def get_cookie_manager() -> stx.CookieManager:
    """Get the cookie manager.

    Returns:
        stx.CookieManager: Cookie manager.
    """
    return stx.CookieManager()


COOKIE_MANAGER: Final[stx.CookieManager] = get_cookie_manager()
DEFAULT_SESSION: Final[dict[str, Any]] = {
    "scramble": parse_scramble(COOKIE_MANAGER.get("scramble_input") or ""),
    "steps": parse_steps(COOKIE_MANAGER.get("steps") or ""),
}
for key, default in DEFAULT_SESSION.items():
    if key not in st.session_state:
        setattr(st.session_state, key, default)


@st.fragment
def get_router() -> stx.Router:
    """Return the router for the app.

    Returns:
        stx.Router: The router.
    """
    return stx.Router(
        {
            "/autotagger": partial(
                autotagger,
                session=st.session_state,
                cookie_manager=COOKIE_MANAGER,
            ),
            "/solver": partial(
                solver,
                session=st.session_state,
                cookie_manager=COOKIE_MANAGER,
            ),
            "/pattern": partial(
                pattern,
                session=st.session_state,
                cookie_manager=COOKIE_MANAGER,
            ),
            "/docs": partial(
                docs,
                session=st.session_state,
                cookie_manager=COOKIE_MANAGER,
            ),
        }
    )


def router() -> None:
    """Page footer with navigation."""
    ROUTER: stx.Router = get_router()
    ROUTER.show_route_view()

    st.markdown("<br><br><br>", unsafe_allow_html=True)

    if "initialized" not in st.session_state:
        st.session_state.__setattr__("initialized", True)
        ROUTER.route("autotagger")

    cols = st.columns([1, 1, 1, 1])

    with cols[0]:
        if st.button(":blue[AUTOTAGGER]", key="autotagger"):
            ROUTER.route("autotagger")
    with cols[1]:
        if st.button(":blue[SOLVER]", key="solver"):
            ROUTER.route("solver")
    with cols[2]:
        if st.button(":blue[PATTERN]", key="pattern"):
            ROUTER.route("pattern")
    with cols[3]:
        if st.button(":blue[DOCS]", key="docs"):
            ROUTER.route("docs")


if __name__ == "__main__":
    configure_logging()
    router()
