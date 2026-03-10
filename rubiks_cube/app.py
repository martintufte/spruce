from __future__ import annotations

import logging
from functools import partial
from typing import Any
from typing import Final

import extra_streamlit_components as stx
import streamlit as st

from rubiks_cube.configuration import APP_CFG
from rubiks_cube.configuration import AppConfig
from rubiks_cube.configuration.logging import configure_logging
from rubiks_cube.pages import app
from rubiks_cube.pages import docs
from rubiks_cube.parsing import parse_scramble
from rubiks_cube.parsing import parse_steps

LOGGER: Final = logging.getLogger(__name__)

st.set_page_config(page_title="Spruce 🌲", layout=APP_CFG.layout)

COOKIE_MANAGER: Final[stx.CookieManager] = stx.CookieManager()

DEFAULT_SESSION: Final[dict[str, Any]] = {
    "scramble": parse_scramble(COOKIE_MANAGER.get(cookie="raw_scramble") or ""),
    "steps": parse_steps(COOKIE_MANAGER.get(cookie="raw_steps") or ""),
    "page": COOKIE_MANAGER.get(cookie="page") or "app",
}

for key, default in DEFAULT_SESSION.items():
    if key not in st.session_state:
        setattr(st.session_state, key, default)


@st.fragment
def get_router(app_cfg: AppConfig, cookie_manager: stx.CookieManager) -> stx.Router:
    return stx.Router(
        {
            "/app": partial(
                app,
                app_cfg=app_cfg,
                session_state=st.session_state,
                cookie_manager=cookie_manager,
            ),
            "/docs": partial(
                docs,
                session_state=st.session_state,
                cookie_manager=cookie_manager,
            ),
        }
    )


def router() -> None:
    """Render current route and initialize default page."""
    router: stx.Router = get_router(app_cfg=APP_CFG, cookie_manager=COOKIE_MANAGER)
    router.show_route_view()

    if "initialized" not in st.session_state:
        st.session_state.initialized = True
        route = st.session_state.get("stx_router_route")
        if route in (None, "/"):
            router.route("app")


if __name__ == "__main__":
    configure_logging(level=APP_CFG.log_level)
    router()
