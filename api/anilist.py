"""
AniList GraphQL API client with SQLite cache.

Cache TTL:
  - media lists (current/planning anime, current manga): 1 hour
  - user stats: 24 hours

Return convention:
  Each public method returns (data, error):
    - (data, None)        — fresh or cached data, no error
    - (data, "Err msg")   — stale cached data returned, API failed
    - (None, "Err msg")   — no cache, API failed
"""
import json
import os
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / '.env')

_TOKEN   = os.getenv('ANILIST_ACCESS_TOKEN', '')
_USER_ID = int(os.getenv('ANILIST_USER_ID', '0'))
_URL     = 'https://graphql.anilist.co'
_DB_PATH = Path(__file__).parent.parent / 'cache' / 'anilist.db'

TTL_LIST  = 3600    # 1 hour
TTL_STATS = 86400   # 24 hours


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


def _cache_get(key: str, ttl: int):
    """Return (data, is_stale). data=None if not found."""
    with _db() as conn:
        row = conn.execute(
            'SELECT data, fetched_at FROM cache WHERE key=?', (key,)
        ).fetchone()
    if row is None:
        return None, True
    data = json.loads(row[0])
    is_stale = (time.time() - row[1]) > ttl
    return data, is_stale


def _cache_set(key: str, data):
    with _db() as conn:
        conn.execute(
            'INSERT OR REPLACE INTO cache (key, data, fetched_at) VALUES (?,?,?)',
            (key, json.dumps(data), int(time.time()))
        )


# ---------------------------------------------------------------------------
# HTTP

def _query(query: str, variables: dict = None):
    """Execute a GraphQL query. Returns parsed JSON or raises on error."""
    headers = {'Content-Type': 'application/json'}
    if _TOKEN:
        headers['Authorization'] = f'Bearer {_TOKEN}'
    resp = requests.post(
        _URL,
        json={'query': query, 'variables': variables or {}},
        headers=headers,
        timeout=10,
    )
    if not resp.ok:
        raise ValueError(f'{resp.status_code}: {resp.text[:300]}')
    body = resp.json()
    if 'errors' in body:
        raise ValueError(body['errors'][0].get('message', 'GraphQL error'))
    return body['data']


def _fetch(cache_key: str, ttl: int, query: str, variables: dict = None):
    """Generic fetch-with-cache. Returns (data, error_or_None)."""
    cached, is_stale = _cache_get(cache_key, ttl)
    if not is_stale:
        return cached, None
    try:
        fresh = _query(query, variables)
        _cache_set(cache_key, fresh)
        return fresh, None
    except Exception as exc:
        err = str(exc)
        if cached is not None:
            return cached, f'API error (cached): {err}'
        return None, f'API error: {err}'


# ---------------------------------------------------------------------------
# Queries

_Q_CURRENT_ANIME = '''
query ($userId: Int) {
  MediaListCollection(userId: $userId, type: ANIME, status: CURRENT) {
    lists {
      entries {
        progress
        media {
          id
          title { romaji english }
          episodes
          nextAiringEpisode {
            airingAt
            timeUntilAiring
            episode
          }
          airingSchedule(notYetAired: false, perPage: 50) {
            nodes { episode airingAt }
          }
        }
      }
    }
  }
}
'''

_Q_PLANNING_ANIME = '''
query ($userId: Int) {
  MediaListCollection(userId: $userId, type: ANIME, status: PLANNING) {
    lists {
      entries {
        media {
          id
          title { romaji english }
          episodes
          startDate { year month day }
          nextAiringEpisode { airingAt episode }
        }
      }
    }
  }
}
'''

_Q_CURRENT_MANGA = '''
query ($userId: Int) {
  MediaListCollection(userId: $userId, type: MANGA, status: CURRENT) {
    lists {
      entries {
        progress
        media {
          id
          title { romaji english }
          chapters
        }
      }
    }
  }
}
'''

_Q_USER_STATS = '''
query {
  Viewer {
    statistics {
      anime { minutesWatched }
      manga { chaptersRead }
    }
  }
}
'''

_Q_COMPLETED_ANIME = '''
query ($userId: Int) {
  MediaListCollection(userId: $userId, type: ANIME, status: COMPLETED) {
    lists {
      entries {
        completedAt { year }
      }
    }
  }
}
'''


# ---------------------------------------------------------------------------
# Public API

def get_current_anime():
    """Currently watching anime with airing schedule. Returns (data, error)."""
    return _fetch('current_anime', TTL_LIST, _Q_CURRENT_ANIME, {'userId': _USER_ID})


def get_planning_anime():
    """Planned anime (upcoming releases). Returns (data, error)."""
    return _fetch('planning_anime', TTL_LIST, _Q_PLANNING_ANIME, {'userId': _USER_ID})


def get_current_manga():
    """Currently reading manga. Returns (data, error)."""
    return _fetch('current_manga', TTL_LIST, _Q_CURRENT_MANGA, {'userId': _USER_ID})


def get_user_stats():
    """User statistics (minutes watched, chapters read). Returns (data, error)."""
    return _fetch('user_stats', TTL_STATS, _Q_USER_STATS)


def get_completed_anime():
    """Completed anime list (for counting completed in current year). Returns (data, error)."""
    return _fetch('completed_anime', TTL_STATS, _Q_COMPLETED_ANIME, {'userId': _USER_ID})
