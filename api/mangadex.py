"""
MangaDex REST API client with SQLite cache.

Auth: OAuth2 password flow (Personal Client).
Access token is cached in SQLite and refreshed automatically via refresh_token.

Cache TTL:
  - reading list:    1 hour
  - chapter feed:    1 hour
  - read markers:    1 hour

Return convention (same as anilist.py):
  Each public method returns (data, error):
    - (data, None)      — fresh or cached data, no error
    - (data, "Err msg") — stale cached data returned, API failed
    - (None, "Err msg") — no cache, API failed
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

_USERNAME      = os.getenv('MANGADEX_USERNAME', '')
_PASSWORD      = os.getenv('MANGADEX_PASSWORD', '')
_CLIENT_ID     = os.getenv('MANGADEX_CLIENT_ID', '')
_CLIENT_SECRET = os.getenv('MANGADEX_CLIENT_SECRET', '')

_API_URL  = 'https://api.mangadex.org'
_AUTH_URL = 'https://auth.mangadex.org/realms/mangadex/protocol/openid-connect/token'
_DB_PATH  = Path(__file__).parent.parent / 'cache' / 'mangadex.db'

TTL = 3600   # 1 hour for all data


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
# Auth — OAuth2 password flow with refresh_token caching

def _get_token() -> str:
    """Return a valid access_token, refreshing or re-authenticating as needed."""
    cached, is_stale = _cache_get('_auth', ttl=0)  # ttl=0: always check expiry manually

    # Try refresh_token if we have one
    if cached and cached.get('refresh_token'):
        expires_at = cached.get('expires_at', 0)
        if time.time() < expires_at - 30:
            return cached['access_token']

        # access_token expired — try refresh
        try:
            resp = requests.post(_AUTH_URL, data={
                'grant_type':    'refresh_token',
                'refresh_token': cached['refresh_token'],
                'client_id':     _CLIENT_ID,
                'client_secret': _CLIENT_SECRET,
            }, timeout=10)
            if resp.ok:
                token_data = resp.json()
                _cache_set('_auth', {
                    'access_token':  token_data['access_token'],
                    'refresh_token': token_data['refresh_token'],
                    'expires_at':    int(time.time()) + token_data['expires_in'],
                })
                return token_data['access_token']
        except Exception:
            pass  # fall through to password auth

    # Full password auth
    resp = requests.post(_AUTH_URL, data={
        'grant_type':    'password',
        'username':      _USERNAME,
        'password':      _PASSWORD,
        'client_id':     _CLIENT_ID,
        'client_secret': _CLIENT_SECRET,
    }, timeout=10)
    if not resp.ok:
        raise ValueError(f'MangaDex auth failed: {resp.status_code}: {resp.text[:200]}')
    token_data = resp.json()
    _cache_set('_auth', {
        'access_token':  token_data['access_token'],
        'refresh_token': token_data['refresh_token'],
        'expires_at':    int(time.time()) + token_data['expires_in'],
    })
    return token_data['access_token']


def _get(path: str, params: dict = None) -> dict:
    """Authenticated GET request. Returns parsed JSON or raises on error."""
    token = _get_token()
    resp = requests.get(
        f'{_API_URL}{path}',
        params=params or {},
        headers={'Authorization': f'Bearer {token}'},
        timeout=10,
    )
    if not resp.ok:
        raise ValueError(f'{resp.status_code}: {resp.text[:200]}')
    return resp.json()


def _fetch(cache_key: str, fetcher) -> tuple:
    """Generic fetch-with-cache. Returns (data, error_or_None)."""
    cached, is_stale = _cache_get(cache_key, TTL)
    if not is_stale:
        return cached, None
    try:
        fresh = fetcher()
        _cache_set(cache_key, fresh)
        return fresh, None
    except Exception as exc:
        err = str(exc)
        if cached is not None:
            return cached, f'API error (cached): {err}'
        return None, f'API error: {err}'


# ---------------------------------------------------------------------------
# Public API

def get_reading_list():
    """
    Manga the user is currently reading.
    Returns (list[{id, title, latest_chapter, read_chapter, has_unread}], error).
    """
    def fetch():
        # Step 1: get all manga with status=reading
        status_data = _get('/manga/status', {'status': 'reading'})
        manga_ids = list((status_data.get('statuses') or {}).keys())
        if not manga_ids:
            return []

        # Step 2: fetch manga details in one batch (up to 100)
        manga_data = _get('/manga', {
            'ids[]':                         manga_ids[:100],
            'limit':                         100,
            'availableTranslatedLanguage[]': 'en',
        })

        # Step 3: for each manga, get latest chapter and read markers
        results = []
        for m in (manga_data.get('data') or []):
            manga_id = m['id']
            attrs    = m.get('attributes') or {}
            title    = (
                (attrs.get('title') or {}).get('en')
                or next(iter((attrs.get('title') or {}).values()), '?')
            )

            # Recent chapters (English, desc) — enough to find last read
            feed = _get(f'/manga/{manga_id}/feed', {
                'translatedLanguage[]': 'en',
                'order[chapter]':       'desc',
                'limit':                100,
            })
            chapters  = feed.get('data') or []
            latest_ch = None
            read_ch   = None
            if chapters:
                latest_ch = (chapters[0].get('attributes') or {}).get('chapter')

            # Read markers — find highest chapter number the user has read
            read_data = _get(f'/manga/{manga_id}/read')
            read_ids  = set(read_data.get('data') or [])
            has_unread = bool(chapters and chapters[0]['id'] not in read_ids)

            for ch in chapters:
                if ch['id'] in read_ids:
                    read_ch = (ch.get('attributes') or {}).get('chapter')
                    break

            results.append({
                'id':             manga_id,
                'title':          title,
                'latest_chapter': latest_ch,  # str or None, e.g. "47"
                'read_chapter':   read_ch,    # str or None — last read chapter
                'has_unread':     has_unread,
            })

        return results

    return _fetch('reading_list', fetch)
