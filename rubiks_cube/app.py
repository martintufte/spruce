from typing import Any
from typing import Final

import streamlit as st
import extra_streamlit_components as stx
from functools import partial

from rubiks_cube.pages import app
from rubiks_cube.pages import docs
from rubiks_cube.pages import patterns
from rubiks_cube.utils.parsing import parse_user_input
from rubiks_cube.utils.parsing import parse_scramble


st.set_page_config(
    page_title="Fewest Moves Solver",
    page_icon="rubiks_cube/data/resources/favicon.png",
)


@st.cache_resource(experimental_allow_widgets=True)
def get_cookie_manager() -> stx.CookieManager:
    return stx.CookieManager()


COOKIE_MANAGER: stx.CookieManager = get_cookie_manager()
DEFAULT_SESSION: Final[dict[str, Any]] = {
    "scramble": parse_scramble(COOKIE_MANAGER.get("scramble_input") or ""),
    "user": parse_user_input(COOKIE_MANAGER.get("user_input") or ""),
}
for key, default in DEFAULT_SESSION.items():
    if key not in st.session_state:
        setattr(st.session_state, key, default)


@st.cache_resource(hash_funcs={"_thread.RLock": lambda _: None})
def get_router() -> stx.Router:
    return stx.Router({
        "/app": partial(
            app,
            session=st.session_state,
            cookie_manager=COOKIE_MANAGER,
        ),
        "/docs": partial(
            docs,
            session=st.session_state,
            cookie_manager=COOKIE_MANAGER,
        ),
        "/patterns": partial(
            patterns,
            session=st.session_state,
            cookie_manager=COOKIE_MANAGER,
        ),
    })


def router() -> None:
    """Page footer with navigation."""
    ROUTER: stx.Router = get_router()
    ROUTER.show_route_view()

    st.write("")
    st.subheader("Links")
    if st.button(":blue[APP]", key="app"):
        ROUTER.route("app")
    if st.button(":blue[DOCS]", key="docs"):
        ROUTER.route("docs")
    if st.button(":blue[PATTERNS]", key="dev"):
        ROUTER.route("patterns")


if __name__ == "__main__":
    router()
