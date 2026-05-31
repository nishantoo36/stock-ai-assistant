"""
Public-safe sentiment contract.

News sentiment is calculated by the private analysis service. This fallback keeps
legacy imports working without exposing sentiment rules.
"""

from __future__ import annotations


def analyze_news_sentiment(news_list: list) -> tuple[int, str, list]:
    detail = [
        {
            "title": item.get("title", ""),
            "link": item.get("link", ""),
            "publisher": item.get("publisher", ""),
            "published": item.get("published", ""),
            "icon": "",
            "signal": "neutral",
            "keywords": "",
        }
        for item in (news_list or [])
    ]
    return 0, "Neutral", detail
