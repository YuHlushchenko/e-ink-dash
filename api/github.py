"""
GitHub GraphQL API client with SQLite cache — powers Screen 1's contribution grid.

Freshness model is push-based, not pull-based: unlike api/anilist.py, there is no TTL
staleness check here. main.py owns the fetch schedule (nightly, hourly maintenance, and
on Screen 1 switch-in) and calls fetch_contributions() explicitly, off the render path,
on a background thread. get_contributions() only ever reads the cache — it must never
make a network call, since screen1.render() runs every minute on the scheduler loop and
a blocking HTTP call there would stall the per-minute clock refresh.

Window: trailing 365 days ending today (matches GitHub's own default contribution-graph
framing) — not a fixed calendar year. Re-fetched on every trigger, so the window slides
forward a day at a time as fetches happen.

Cache shape: {'total': int, 'days': {'YYYY-MM-DD': 'NONE'|'FIRST_QUARTILE'|...|'FOURTH_QUARTILE'}}
"""
import json
import os
import sqlite3
import time
from contextlib import contextmanager
from datetime import date, timedelta
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / '.env')

_TOKEN    = os.getenv('GITHUB_TOKEN', '')
_USERNAME = os.getenv('GITHUB_USERNAME', '')
_URL      = 'https://api.github.com/graphql'
_DB_PATH  = Path(__file__).parent.parent / 'cache' / 'github.db'


# ---------------------------------------------------------------------------
# Cache (SQLite key/value)

@contextmanager
def _db():
    _DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(_DB_PATH)
    conn.execute('''CREATE TABLE IF NOT EXISTS cache (
        key        TEXT PRIMARY KEY,
        data       TEXT NOT NULL,
        fetched_at INTEGER NOT NULL
    )''')
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _cache_get_raw(key: str):
    """Return cached data regardless of age, or None if never fetched."""
    with _db() as conn:
        row = conn.execute(
            'SELECT data FROM cache WHERE key=?', (key,)
        ).fetchone()
    return json.loads(row[0]) if row else None


def _cache_set(key: str, data):
    with _db() as conn:
        conn.execute(
            'INSERT OR REPLACE INTO cache (key, data, fetched_at) VALUES (?,?,?)',
            (key, json.dumps(data), int(time.time()))
        )


# ---------------------------------------------------------------------------
# HTTP

_Q_CONTRIBUTIONS = '''
query ($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            date
            contributionLevel
          }
        }
      }
    }
  }
}
'''


def _query(variables: dict):
    """Execute the contributions GraphQL query. Returns parsed JSON or raises on error."""
    headers = {'Content-Type': 'application/json'}
    if _TOKEN:
        headers['Authorization'] = f'Bearer {_TOKEN}'
    resp = requests.post(
        _URL,
        json={'query': _Q_CONTRIBUTIONS, 'variables': variables},
        headers=headers,
        timeout=10,
    )
    if not resp.ok:
        raise ValueError(f'{resp.status_code}: {resp.text[:300]}')
    body = resp.json()
    if 'errors' in body:
        raise ValueError(body['errors'][0].get('message', 'GraphQL error'))
    return body['data']


def _flatten(raw: dict) -> dict:
    """user.contributionsCollection.contributionCalendar -> {'total': int, 'days': {date: level}}."""
    calendar = raw['user']['contributionsCollection']['contributionCalendar']
    days = {
        day['date']: day['contributionLevel']
        for week in calendar['weeks']
        for day in week['contributionDays']
    }
    return {'total': calendar['totalContributions'], 'days': days}


# ---------------------------------------------------------------------------
# Public API

_CACHE_KEY = 'contributions_rolling'


def get_contributions():
    """
    Cache-only read — never makes a network call. Safe to call from the render path.
    Returns ({'total': int, 'days': {'YYYY-MM-DD': level}}, None), or (None, None) if
    nothing has been fetched yet.
    """
    return _cache_get_raw(_CACHE_KEY), None


def fetch_contributions():
    """
    Network fetch + cache write for the trailing 365 days ending today. Not called from
    the render path — main.py runs this on a background thread at its scheduled trigger
    points (nightly, hourly, Screen 1 switch-in). Returns (data, error_or_None); on error
    the cache is left untouched, so get_contributions() keeps serving the last good
    snapshot until the next successful fetch.
    """
    today = date.today()
    window_start = today - timedelta(days=364)
    from_ts = f'{window_start.isoformat()}T00:00:00Z'
    to_ts   = f'{today.isoformat()}T23:59:59Z'
    try:
        raw = _query({'login': _USERNAME, 'from': from_ts, 'to': to_ts})
        fresh = _flatten(raw)
        _cache_set(_CACHE_KEY, fresh)
        return fresh, None
    except Exception as exc:
        return None, f'API error: {exc}'
