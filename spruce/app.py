from __future__ import annotations

import logging
from functools import partial
from typing import Any
from typing import Final

import extra_streamlit_components as stx
import streamlit as st
from annotated_text import parameters

from spruce.configuration import APP_CFG
from spruce.configuration import AppConfig
from spruce.configuration.logging import configure_logging
from spruce.configuration.paths import OUTPUT_DIR
from spruce.move.meta import MoveMeta
from spruce.pages import app
from spruce.pages import docs
from spruce.parsing import parse_scramble
from spruce.parsing import parse_steps
from spruce.serialization.converter import create_converter
from spruce.serialization.resources import ResourceHandler
from spruce.serialization.utils import create_session_id

LOGGER: Final = logging.getLogger(__name__)

st.set_page_config(page_title="Spruce 🌲", layout=APP_CFG.layout)

parameters.PADDING = "0.25rem 0.4rem"  # ty: ignore[invalid-assignment]
parameters.SHOW_LABEL_SEPARATOR = False  # ty: ignore[invalid-assignment]

COOKIE_MANAGER: Final[stx.CookieManager] = stx.CookieManager()
MOVE_META: Final[MoveMeta] = MoveMeta.from_puzzle(puzzle=APP_CFG.puzzle)

DEFAULT_SESSION: Final[dict[str, Any]] = {
    "scramble": parse_scramble(
        COOKIE_MANAGER.get(cookie="raw_scramble") or "", move_meta=MOVE_META
    ),
    "steps": parse_steps(COOKIE_MANAGER.get(cookie="raw_steps") or "", move_meta=MOVE_META),
    "page": COOKIE_MANAGER.get(cookie="page") or "app",
}

for key, default in DEFAULT_SESSION.items():
    if key not in st.session_state:
        setattr(st.session_state, key, default)

if "resource_handler" not in st.session_state:
    session_id = create_session_id()
    handler = ResourceHandler(resource_dir=OUTPUT_DIR / session_id, converter=create_converter())
    handler.save_config(APP_CFG)
    st.session_state.resource_handler = handler


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
        },
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
