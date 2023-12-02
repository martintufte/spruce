from typing import Any


def exists(x: Any | None) -> bool:
    """The exists function."""
    return x is not None


def default(x: Any, default_value) -> Any:
    """The default function."""
    return x if exists(x) else default_value
