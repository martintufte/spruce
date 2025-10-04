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
    layout="centered",
    initial_sidebar_state="expanded",
)

# Custom CSS for sleek sidebar styling
st.markdown(
    """
<style>
    /* Prevent sidebar color changes during drag/resize */
    .stSidebar {
        background-color: #fafafa !important;
    }

    .stSidebar > div:first-child {
        background-color: #fafafa !important;
        padding: 1rem 0;
    }

    .stSidebar .stSidebar-content {
        background-color: #fafafa !important;
    }

    /* Prevent any brown/theme color overrides */
    .stSidebar * {
        background-color: inherit !important;
    }

    .stSidebar h1 {
        text-align: center;
        color: #333333 !important;
        margin-bottom: 1rem;
        background-color: transparent !important;
    }

    /* Regular button styling */
    .stButton > button {
        width: 100%;
        border-radius: 12px;
        border: none;
        font-weight: 500;
        font-size: 14px;
        padding: 0.75rem 1.25rem;
        background-color: transparent !important;
        color: #666666 !important;
        transition: all 0.2s ease;
        text-align: left;
        margin-bottom: 0.25rem;
    }

    .stButton > button:hover {
        background-color: #f0f0f0 !important;
        color: #333333 !important;
        transform: translateX(2px);
    }

    /* Active button styling - more vibrant and persistent */
    .stButton > button[data-baseweb="button"][data-kind="primary"] {
        background-color: #10b981 !important;
        background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
        color: white !important;
        font-weight: 700 !important;
        box-shadow: 0 4px 20px rgba(16, 185, 129, 0.4) !important;
        border: 2px solid #059669 !important;
        transform: translateX(2px) !important;
    }

    .stButton > button[data-baseweb="button"][data-kind="primary"]:hover {
        background-color: #059669 !important;
        background: linear-gradient(135deg, #059669 0%, #047857 100%) !important;
        transform: translateX(3px) !important;
        box-shadow: 0 6px 25px rgba(16, 185, 129, 0.5) !important;
        border: 2px solid #047857 !important;
    }

    /* Ensure no color changes during interactions */
    .stButton > button[data-baseweb="button"][data-kind="primary"]:active,
    .stButton > button[data-baseweb="button"][data-kind="primary"]:focus {
        background-color: #10b981 !important;
        background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
        color: white !important;
        border: 2px solid #059669 !important;
    }
</style>
""",
    unsafe_allow_html=True,
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
    """Main app with sidebar navigation."""
    router: stx.Router = get_router()

    # Initialize with default route
    if "initialized" not in st.session_state:
        st.session_state.__setattr__("initialized", True)
        st.session_state.__setattr__("current_route", "autotagger")
        router.route("autotagger")

    # Sidebar navigation
    with st.sidebar:
        st.title("Rubik's Cube")
        st.markdown("---")

        # Get current route to highlight active page
        current_route = getattr(st.session_state, "current_route", "autotagger")

        # Sleek navigation buttons without icons
        if st.button(
            "Autotagger",
            key="autotagger",
            use_container_width=True,
            type="primary" if current_route == "autotagger" else "secondary",
        ):
            st.session_state.current_route = "autotagger"
            router.route("autotagger")

        if st.button(
            "Solver",
            key="solver",
            use_container_width=True,
            type="primary" if current_route == "solver" else "secondary",
        ):
            st.session_state.current_route = "solver"
            router.route("solver")

        if st.button(
            "Pattern",
            key="pattern",
            use_container_width=True,
            type="primary" if current_route == "pattern" else "secondary",
        ):
            st.session_state.current_route = "pattern"
            router.route("pattern")

        if st.button(
            "Docs",
            key="docs",
            use_container_width=True,
            type="primary" if current_route == "docs" else "secondary",
        ):
            st.session_state.current_route = "docs"
            router.route("docs")

        st.markdown("---")
        st.caption("by Martin Tufte, 2025")

    # Main content area
    router.show_route_view()


if __name__ == "__main__":
    configure_logging()
    router()
