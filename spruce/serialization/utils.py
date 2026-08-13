from __future__ import annotations

from datetime import datetime


def create_session_id() -> str:
    return datetime.now().astimezone().strftime("%y%m%d%H%M%S")
