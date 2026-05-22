"""
Small shared helpers used across Streamlit UI modules.
"""

from __future__ import annotations

from typing import Any


def attr(obj: Any, name: str, default: Any = None) -> Any:
    """Read an attribute from either a plain dict or an object."""
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def query_param(query_params: Any, name: str) -> str | None:
    """Return the first Streamlit query param value for a key."""
    value = query_params.get(name)
    if isinstance(value, list):
        return value[0] if value else None
    return value
