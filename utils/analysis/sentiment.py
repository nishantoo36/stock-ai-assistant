"""
Keyword-based news sentiment scorer.
Returns a sentiment score, label, and per-article detail list.
"""

POSITIVE_WORDS = [
    "beat","beats","surge","surges","rally","gain","gains","growth","profit","profits",
    "record","strong","upgrade","upgraded","outperform","bullish","partnership",
    "expansion","breakthrough","revenue","rises","jumps","soars","climbs","boosts",
    "wins","positive","optimistic","upside","recovery","rebound","dividend",
    "exceeded","exceeds","higher","increase","milestone","opportunity","confident",
    "momentum","demand","innovative","leading","approval","approved","deal",
    "acquisition","buyback","surprise","above",
]

NEGATIVE_WORDS = [
    "loss","losses","crash","crashes","decline","falls","drops","downgrade",
    "downgraded","sell","bearish","fraud","lawsuit","scandal","misses","miss",
    "weak","cut","layoff","layoffs","investigation","recall","plunges","tumbles",
    "slumps","warning","risk","concern","debt","bankrupt","default","disappointing",
    "lower","below","penalty","fine","shortage","inflation","recession",
    "withdrawn","suspended","halt","probe","crisis","conflict","uncertainty",
    "hurt","pressure","fell","sank",
]

# Maps net score → (signal_value, label)
_SCORE_MAP = [
    ( 5,  2, "Very Positive"),
    ( 2,  1, "Positive"),
    (-2,  0, "Neutral"),       # between -2 and +2
    (-5, -1, "Negative"),
    (None,-2, "Very Negative"),
]


def analyze_news_sentiment(news_list: list) -> tuple[int, str, list]:
    """
    Returns:
        score    : int  -2 … +2
        label    : str  e.g. "Positive"
        detail   : list of dicts with keys title, link, publisher,
                   icon, signal, keywords
    """
    if not news_list:
        return 0, "Neutral", []

    total_pos = total_neg = 0
    detail: list[dict] = []

    for article in news_list:
        title_lower = article.get("title", "").lower()
        pos_hits = [w for w in POSITIVE_WORDS if w in title_lower]
        neg_hits = [w for w in NEGATIVE_WORDS if w in title_lower]

        entry = {
            "title":     article.get("title", "")[:100],
            "link":      article.get("link", ""),
            "publisher": article.get("publisher", ""),
            "published": article.get("published", ""),
        }

        if pos_hits:
            total_pos += len(pos_hits)
            entry.update(icon="✅", signal="positive", keywords=", ".join(pos_hits[:3]))
        elif neg_hits:
            total_neg += len(neg_hits)
            entry.update(icon="🔴", signal="negative", keywords=", ".join(neg_hits[:3]))
        else:
            entry.update(icon="⚪", signal="neutral", keywords="")

        detail.append(entry)

    net = total_pos - total_neg

    if   net >= 5:  return  2, "Very Positive", detail
    elif net >= 2:  return  1, "Positive",      detail
    elif net <= -5: return -2, "Very Negative", detail
    elif net <= -2: return -1, "Negative",      detail
    else:           return  0, "Neutral",       detail
