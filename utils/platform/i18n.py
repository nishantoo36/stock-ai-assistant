"""
Internationalization (i18n) module for dynamic language support.
Provides translation functions and language management for Streamlit app.
Supports: English, Hindi, Gujarati, French
"""

import os
import json
import streamlit as st
from typing import Dict, Any

from utils.platform.common import query_param

# ── Configuration ────────────────────────────────────────────────────────────

TRANSLATIONS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "translations")
SUPPORTED_LANGUAGES = {
    "en": "English",
    "hi": "हिंदी",
    "gu": "ગુજરાતી",
    "fr": "Français",
}

# ── Translation Cache ────────────────────────────────────────────────────────

_translation_cache: Dict[str, Dict[str, Any]] = {}


def _load_translations(lang_code: str) -> Dict[str, Any]:
    """Load translation file for a given language. Uses cache if available."""
    if lang_code in _translation_cache:
        return _translation_cache[lang_code]

    trans_file = os.path.join(TRANSLATIONS_DIR, f"{lang_code}.json")
    
    if not os.path.exists(trans_file):
        # Fallback to English if language file not found
        if lang_code != "en":
            return _load_translations("en")
        return {}
    
    try:
        with open(trans_file, "r", encoding="utf-8") as f:
            translations = json.load(f)
            _translation_cache[lang_code] = translations
            return translations
    except (json.JSONDecodeError, IOError) as e:
        st.warning(f"Error loading translations for {lang_code}: {e}")
        return {}


def set_language(lang_code: str) -> None:
    """Set the current language in session state."""
    if lang_code in SUPPORTED_LANGUAGES:
        st.session_state.current_language = lang_code
        try:
            if query_param(st.query_params, "lang") != lang_code:
                st.query_params["lang"] = lang_code
        except Exception:
            pass
    else:
        st.warning(f"Language {lang_code} not supported. Falling back to English.")
        st.session_state.current_language = "en"


def get_current_language() -> str:
    """Get the current language from session state, with fallback to 'en'."""
    if "current_language" not in st.session_state:
        # Check URL query param for language preference
        lang_from_url = query_param(st.query_params, "lang") or "en"
        
        if lang_from_url in SUPPORTED_LANGUAGES:
            st.session_state.current_language = lang_from_url
        else:
            st.session_state.current_language = "en"
    
    return st.session_state.current_language


def t(key: str, **kwargs) -> str:
    """
    Translate a key to the current language.
    Supports nested keys using dot notation: "section.subsection.key"
    Supports value interpolation using {} placeholders in translation strings.
    
    Args:
        key: Translation key (dot-separated for nested keys)
        **kwargs: Values to interpolate into translation string
    
    Returns:
        Translated string, or key itself if not found (with warning)
    """
    current_lang = get_current_language()
    translations = _load_translations(current_lang)
    
    # Navigate nested dictionary using dot notation
    keys = key.split(".")
    value = translations
    for k in keys:
        if isinstance(value, dict):
            value = value.get(k)
        else:
            value = None
            break
    
    # If key not found in current language, try English
    if value is None and current_lang != "en":
        translations = _load_translations("en")
        value = translations
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                value = None
                break
    
    # If still not found, return the key itself
    if value is None:
        st.warning(f"Translation missing for key: {key}")
        return key
    
    # Convert to string if necessary
    value_str = str(value)
    
    # Interpolate values if kwargs provided
    if kwargs:
        try:
            value_str = value_str.format(**kwargs)
        except KeyError as e:
            st.warning(f"Missing interpolation value for {e} in key {key}")
    
    return value_str


def get_available_languages() -> Dict[str, str]:
    """Get dictionary of available languages with their display names."""
    return SUPPORTED_LANGUAGES.copy()


def get_language_display_name(lang_code: str) -> str:
    """Get the display name for a language code."""
    return SUPPORTED_LANGUAGES.get(lang_code, lang_code)


def get_language_flag(lang_code: str) -> str:
    """Get the flag emoji for a language code."""
    flags = {
        "en": "🇬🇧",
        "hi": "🇮🇳",
        "gu": "🇮🇳",
        "fr": "🇫🇷",
    }
    return flags.get(lang_code, "🌐")
