from __future__ import annotations

from functools import partial
from typing import Any
from typing import Final

import extra_streamlit_components as stx
import streamlit as st

from rubiks_cube.configuration.logging import configure_logging
from rubiks_cube.configuration.paths import DATA_DIR
from rubiks_cube.pages import beam_search
from rubiks_cube.pages import docs
from rubiks_cube.pages import solver
from rubiks_cube.parsing import parse_scramble
from rubiks_cube.parsing import parse_steps

st.set_page_config(
    page_title="Spruce",
    page_icon=DATA_DIR / "favicon.png",
)


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
    "page": COOKIE_MANAGER.get("page") or "solver",
}
for key, default in DEFAULT_SESSION.items():
    if key not in st.session_state:
        setattr(st.session_state, key, default)


@st.fragment
def get_router() -> stx.Router:
    """Return the router for the app."""
    return stx.Router(
        {
            "/solver": partial(
                solver,
                session=st.session_state,
                cookie_manager=COOKIE_MANAGER,
            ),
            "/beam-search": partial(
                beam_search,
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
    router: stx.Router = get_router()
    router.show_route_view()
    st.markdown("<br><br><br>", unsafe_allow_html=True)

    if "initialized" not in st.session_state:
        st.session_state.__setattr__("initialized", True)
        router.route("solver")

    cols = st.columns([1, 1, 1])

    with cols[0]:
        if st.button(":blue[SOLVER]", key="solver"):
            COOKIE_MANAGER.set("page", "solver")
            router.route("solver")

    with cols[1]:
        if st.button(":blue[BEAM SEARCH]", key="beam-search"):
            COOKIE_MANAGER.set("page", "beam-search")
            router.route("beam-search")

    with cols[2]:
        if st.button(":blue[DOCS]", key="docs"):
            COOKIE_MANAGER.set("page", "docs")
            router.route("docs")


if __name__ == "__main__":
    configure_logging()
    router()
