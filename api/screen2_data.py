"""
Transform AniList API responses into card-ready dicts for Screen 2.

Public functions — all return (list_or_dict, error_or_None):
  get_upcoming_releases() -> list[dict]   release_card fields
  get_upcoming_episodes() -> list[dict]   upcoming_card fields
  get_queue()             -> list[dict]   queue_card fields
  get_manga_updates()     -> list[dict]   manga_card fields
  get_stats()             -> dict         footer stats
"""
import time
from datetime import date, datetime

from api.anilist import (
    get_current_anime,
    get_planning_anime,
    get_current_manga,
    get_user_stats,
    get_completed_anime,
)


# ---------------------------------------------------------------------------
# Helpers

def _fmt_duration(seconds: int) -> str:
    """Format seconds into '1d 4h' or '2h 30m'."""
    if seconds <= 0:
        return 'now'
    days  = seconds // 86400
    hours = (seconds % 86400) // 3600
    mins  = (seconds % 3600) // 60
    if days >= 1:
        return f'{days}d {hours}h'
    return f'{hours}h {mins}m'


_MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
           'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']


def _fmt_date_short(ts: int) -> str:
    """Unix timestamp → 'Mar 15' (locale-independent)."""
    dt = datetime.fromtimestamp(ts)
    return f'{_MONTHS[dt.month - 1]} {dt.day}'


def _fmt_date_long(ts: int) -> str:
    """Unix timestamp → 'Mar 15, 2025' (locale-independent)."""
    dt = datetime.fromtimestamp(ts)
    return f'{_MONTHS[dt.month - 1]} {dt.day}, {dt.year}'


def _ts_to_date(ts: int) -> date:
    return datetime.fromtimestamp(ts).date()


_TITLE_SUBS = str.maketrans({
    '【': '[',  '】': ']',   # lenticular brackets
    '「': "'",  '」': "'",   # corner brackets
    '『': '[',  '』': ']',   # white corner brackets
    '（': '(',  '）': ')',   # full-width parens
    '・': '.',  '〜': '~',   # CJK middle dot, wave dash
    '★': '*',   '☆': '*',   # filled/empty star
    '♪': '',    '♥': '',    # music note, heart
    '―': '-',                # horizontal bar
})


def _title(media) -> str:
    t = media['title'].get('english') or media['title']['romaji'] or '?'
    return t.translate(_TITLE_SUBS)


def _entries(data) -> list:
    """Flatten MediaListCollection.lists[].entries into a single list."""
    if data is None:
        return []
    result = []
    for lst in (data.get('MediaListCollection') or {}).get('lists', []):
        result.extend(lst.get('entries', []))
    return result


# ---------------------------------------------------------------------------
# Public API

def get_upcoming_releases():
    """
    Planning anime that have a nextAiringEpisode (season is about to start).
    Sorted by airing date ascending.
    Returns (list[{title, eps_count, starts_in, final_ep, airing_date}], error).
    """
    data, err = get_planning_anime()
    entries = _entries(data)
    now = int(time.time())

    items = []
    for e in entries:
        m   = e['media']
        nae = m.get('nextAiringEpisode')
        if not nae:
            continue

        airing_at     = nae['airingAt']
        seconds_until = max(0, airing_at - now)
        total_eps     = m.get('episodes')
        next_ep       = nae['episode']

        if total_eps and next_ep:
            final_ep = _fmt_date_short(airing_at + (total_eps - next_ep) * 7 * 86400)
        else:
            final_ep = '?'

        items.append({
            'title':       _title(m),
            'eps_count':   total_eps if total_eps else '?',
            'starts_in':   _fmt_duration(seconds_until),
            'final_ep':    final_ep,
            'airing_date': _ts_to_date(airing_at),
        })

    items.sort(key=lambda x: x['airing_date'])
    return items, err


def get_upcoming_episodes():
    """
    Currently watching anime that still have upcoming episodes.
    Sorted by next airing date ascending.
    Returns (list[{title, ep_label, time_until, final_date, watched, total,
                   behind, highlight, airing_date}], error).
    """
    data, err = get_current_anime()
    entries = _entries(data)
    now = int(time.time())

    items = []
    for e in entries:
        m   = e['media']
        nae = m.get('nextAiringEpisode')
        if not nae:
            continue  # fully aired → goes to queue

        airing_at     = nae['airingAt']
        next_ep       = nae['episode']
        seconds_until = max(0, airing_at - now)
        progress      = e.get('progress') or 0
        total_eps     = m.get('episodes') or 0
        behind        = max(0, (next_ep - 1) - progress)
        is_final      = bool(total_eps and next_ep == total_eps)
        ep_label      = 'FINAL' if is_final else f'{next_ep} ep'

        if total_eps and total_eps > next_ep:
            final_date = _fmt_date_short(airing_at + (total_eps - next_ep) * 7 * 86400)
        elif is_final:
            final_date = _fmt_date_short(airing_at)
        else:
            final_date = '∞'

        # progress bar total: known total, or estimate from what we know
        bar_total = total_eps if total_eps else max(next_ep, progress + behind + 1)

        items.append({
            'title':       _title(m),
            'ep_label':    ep_label,
            'time_until':  _fmt_duration(seconds_until),
            'final_date':  final_date,
            'watched':     progress,
            'total':       bar_total,
            'behind':      behind,
            'highlight':   is_final,
            'airing_date': _ts_to_date(airing_at),
        })

    items.sort(key=lambda x: x['airing_date'])
    return items, err


def get_queue():
    """
    Currently watching anime with no nextAiringEpisode (show finished airing).
    Sorted by most recently updated first.
    Returns (list[{title, watched, total, last_updated}], error).
    """
    data, err = get_current_anime()
    entries = _entries(data)

    items = []
    for e in entries:
        m = e['media']
        if m.get('nextAiringEpisode'):
            continue  # still airing → upcoming episodes

        progress   = e.get('progress') or 0
        total_eps  = m.get('episodes') or 0
        updated_at = e.get('updatedAt') or 0

        items.append({
            'title':        _title(m),
            'watched':      progress,
            'total':        total_eps if total_eps else progress,
            'last_updated': _fmt_date_long(updated_at) if updated_at else '—',
            '_sort':        updated_at,
        })

    items.sort(key=lambda x: -x.pop('_sort'))
    return items, err


def get_manga_updates():
    """
    Currently reading manga. Sorted by most unread chapters first.
    Returns (list[{title, current_ch, total_ch, status}], error).
    """
    data, err = get_current_manga()
    entries = _entries(data)

    items = []
    for e in entries:
        m         = e['media']
        progress  = e.get('progress') or 0
        total_ch  = m.get('chapters') or 0
        new_chs   = max(0, total_ch - progress) if total_ch else 0

        if not total_ch:
            status = 'Ongoing'
        elif new_chs == 0:
            status = 'Up to date'
        elif new_chs == 1:
            status = 'New chapter available'
        else:
            status = f'{new_chs} new chapters'

        items.append({
            'title':      _title(m),
            'current_ch': progress,
            'total_ch':   total_ch if total_ch else max(progress, 1),
            'status':     status,
            '_sort':      new_chs,
        })

    items.sort(key=lambda x: -x.pop('_sort'))
    return items, err


def get_stats():
    """
    Aggregate stats for the footer bar.
    Returns ({watching, planning, completed_year, total_hours, manga_chapters}, error).
    """
    current_data,   err1 = get_current_anime()
    planning_data,  err2 = get_planning_anime()
    stats_data,     err3 = get_user_stats()
    completed_data, err4 = get_completed_anime()
    manga_data,     err5 = get_current_manga()

    watching = len(_entries(current_data))
    planning = len(_entries(planning_data))

    current_year   = datetime.now().year
    completed_year = 0
    minutes_this_year = 0
    for e in _entries(completed_data):
        if (e.get('completedAt') or {}).get('year') == current_year:
            completed_year += 1
            m = e.get('media') or {}
            minutes_this_year += (m.get('episodes') or 0) * (m.get('duration') or 0)

    # Add currently watching: progress × duration
    for e in _entries(current_data):
        progress = e.get('progress') or 0
        duration = (e.get('media') or {}).get('duration') or 0
        minutes_this_year += progress * duration

    chapters_read = 0
    if stats_data:
        viewer = (stats_data.get('Viewer') or {})
        stats  = (viewer.get('statistics') or {})
        chapters_read = (stats.get('manga') or {}).get('chaptersRead') or 0

    # Fallback for new users: sum progress from current manga
    if chapters_read == 0:
        for e in _entries(manga_data):
            chapters_read += e.get('progress') or 0

    errors = [e for e in [err1, err2, err3, err4, err5] if e]
    return {
        'watching':       watching,
        'planning':       planning,
        'completed_year': completed_year,
        'total_hours':    minutes_this_year // 60,
        'manga_chapters': chapters_read,
    }, (errors[0] if errors else None)
