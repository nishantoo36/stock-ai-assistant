"""
Small shared helpers used across Streamlit UI modules.
"""

from __future__ import annotations

from typing import Any

import streamlit as st


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


def select_stock(ticker: str, company_name: str) -> None:
    """Update session state and URL for a selected stock without changing tabs."""
    st.session_state.selected_ticker = ticker
    st.session_state.company_name = company_name
    st.session_state.search_no_results = None
    st.session_state.url_selected_stock = True
    st.session_state.reset_search_query = False
    st.query_params["stock"] = ticker
    st.query_params["company"] = company_name
