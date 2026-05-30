"""
Shared SQLite cache — all Streamlit user sessions on the same
server read from and write to the same on-disk DB, so Yahoo
Finance is only hit once per ticker per TTL window regardless
of how many concurrent users there are.
"""

import sqlite3
import json
import time
import threading

DB_PATH  = "/tmp/stock_cache.db"

TTL_INFO    = 3600   # stock info    — 1 hour
TTL_HISTORY = 900    # price history — 15 mins
TTL_NEWS    = 1800   # news          — 30 mins
TTL_SEARCH  = 1800   # search        — 30 mins

_db_lock = threading.Lock()


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS cache (
            key        TEXT PRIMARY KEY,
            value      TEXT NOT NULL,
            fetched_at REAL NOT NULL
        )
    """)
    conn.commit()
    return conn


def cache_get(key: str, ttl: int):
    """Return parsed value if still within TTL, else None."""
    try:
        with _db_lock:
            conn = _get_conn()
            row  = conn.execute(
                "SELECT value, fetched_at FROM cache WHERE key=?", (key,)
            ).fetchone()
            conn.close()
        if row and (time.time() - row[1]) < ttl:
            return json.loads(row[0])
    except Exception:
        pass
    return None


def cache_get_stale(key: str):
    """Return any cached value regardless of age (for stale-while-revalidate)."""
    try:
        with _db_lock:
            conn = _get_conn()
            row  = conn.execute(
                "SELECT value FROM cache WHERE key=?", (key,)
            ).fetchone()
            conn.close()
        if row:
            return json.loads(row[0])
    except Exception:
        pass
    return None


def cache_set(key: str, value) -> None:
    """Persist value to the shared cache."""
    try:
        with _db_lock:
            conn = _get_conn()
            conn.execute(
                "INSERT OR REPLACE INTO cache (key, value, fetched_at) VALUES (?,?,?)",
                (key, json.dumps(value, default=str), time.time())
            )
            conn.commit()
            conn.close()
    except Exception:
        pass


def fetch_in_background(fn, cache_key: str, *args) -> None:
    """Run fn(*args) in a daemon thread and store the result in cache."""
    def _run():
        try:
            result = fn(*args)
            if result is not None:
                cache_set(cache_key, result)
        except Exception:
            pass
    threading.Thread(target=_run, daemon=True).start()
