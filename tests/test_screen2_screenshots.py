"""
Screen 2 screenshot tests — no hardware, no API calls needed.

All data is mocked via monkeypatching api.screen2_data functions.
Output: tests/output/screen2_*.png

Run:
    python3 tests/test_screen2_screenshots.py
"""
import sys
from datetime import date
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from PIL import Image
import api.screen2_data as data_layer

OUT_DIR = Path(__file__).parent / 'output'
OUT_DIR.mkdir(exist_ok=True)

class FakeRenderer:
    width  = 800
    height = 480

from screens.screen2 import Screen2
renderer = FakeRenderer()
screen   = Screen2(renderer)

# ---------------------------------------------------------------------------
# Mock data builders

_STATS = {'watching': 12, 'planning': 5, 'completed_year': 8,
          'total_hours': 142, 'manga_reading': 3}

def _release(title, starts_in, eps='?', final_ep='?', d=date(2026, 4, 1)):
    return {'title': title, 'eps_count': eps, 'starts_in': starts_in,
            'final_ep': final_ep, 'airing_date': d, 'airing_at': 0}

def _episode(title, ep_label, time_until, watched, total,
             behind=0, highlight=False, final_date='∞', d=date(2026, 4, 5)):
    return {'title': title, 'ep_label': ep_label, 'time_until': time_until,
            'final_date': final_date, 'watched': watched, 'total': total,
            'behind': behind, 'highlight': highlight,
            'airing_date': d, 'airing_at': 0}

def _queue(title, watched, total, updated='Mar 10, 2026'):
    return {'title': title, 'watched': watched, 'total': total, 'last_updated': updated}

def _manga(title, current_ch, total_ch, status):
    return {'title': title, 'current_ch': current_ch,
            'total_ch': total_ch, 'status': status}

# ---------------------------------------------------------------------------
# Patch + render helper

def _render(label, releases, episodes, queue, manga, stats=None,
            err_rel=None, err_ep=None, err_q=None, err_mg=None):
    data_layer.get_upcoming_releases = lambda: (releases, err_rel)
    data_layer.get_upcoming_episodes = lambda: (episodes, err_ep)
    data_layer.get_queue            = lambda: (queue,    err_q)
    data_layer.get_manga_updates    = lambda: (manga,    err_mg)
    data_layer.get_stats            = lambda: (stats or _STATS, None)

    img = screen.render()
    bw  = img.convert('1', dither=Image.FLOYDSTEINBERG).convert('L')
    bw.save(OUT_DIR / f'screen2_{label}.png')
    print(f'  ✓  {label}')

# ---------------------------------------------------------------------------
# Test cases

# 1. Typical mixed state
_render('typical',
    releases=[
        _release('Dungeon Meshi S2', '3d 4h', eps=12, final_ep='Jun 15'),
        _release('Solo Leveling S3', '5d 2h', eps=13),
    ],
    episodes=[
        _episode('Frieren', '4 ep', '1d 6h', watched=3, total=28),
        _episode('One Piece', '5 ep', '2d 3h', watched=4, total=1100, behind=2),
        _episode('Bleach TYBW', '3 ep', '3d 0h', watched=2, total=21),
    ],
    queue=[
        _queue('Attack on Titan', 87, 87),
        _queue('Demon Slayer S3', 11, 11),
    ],
    manga=[
        _manga('Berserk', 374, 400, '+2 new'),
        _manga('Vagabond', 327, 327, 'Up to date'),
    ],
)

# 2. Final episode — highlighted black card
_render('final_episode',
    releases=[],
    episodes=[
        _episode('Frieren', 'FINAL', '0h 45m', watched=27, total=28,
                 highlight=True, final_date='Mar 13, 2026', d=date(2026, 3, 13)),
        _episode('Bleach TYBW', '21 ep', '3d 0h', watched=20, total=21),
    ],
    queue=[_queue('Attack on Titan', 87, 87)],
    manga=[_manga('Berserk', 374, 400, '+2 new')],
)

# 3. Behind on multiple episodes
_render('behind_episodes',
    releases=[],
    episodes=[
        _episode('One Piece', '1105 ep', '2h 30m', watched=948, total=1100, behind=156),
        _episode('Naruto', '50 ep',    '1d 2h',  watched=30,  total=220,  behind=19),
        _episode('Bleach', '15 ep',    '3d 0h',  watched=10,  total=21,   behind=4),
    ],
    queue=[],
    manga=[],
)

# 4. Imminent timers (hours/minutes)
_render('timer_imminent',
    releases=[
        _release('Solo Leveling S3', '0h 30m', d=date(2026, 3, 13)),
    ],
    episodes=[
        _episode('Frieren', '4 ep', '0h 45m', watched=3, total=28, d=date(2026, 3, 13)),
        _episode('One Piece', '5 ep', '2h 10m', watched=4, total=1100, d=date(2026, 3, 13)),
    ],
    queue=[_queue('Attack on Titan', 87, 87)],
    manga=[_manga('Berserk', 374, 400, '+2 new')],
)

# 5. Timer = "now" (just aired, cache not yet refreshed)
_render('timer_now',
    releases=[],
    episodes=[
        _episode('Frieren', 'FINAL', 'now', watched=27, total=28,
                 highlight=True, final_date='Mar 13, 2026'),
        _episode('One Piece', '1105 ep', '6d 23h', watched=948, total=1100),
    ],
    queue=[_queue('Attack on Titan', 87, 87)],
    manga=[],
)

# 6. All columns empty
_render('all_empty',
    releases=[],
    episodes=[],
    queue=[],
    manga=[],
    stats={'watching': 0, 'planning': 0, 'completed_year': 0,
           'total_hours': 0, 'manga_reading': 0},
)

# 7. API errors
_render('api_error',
    releases=[], episodes=[], queue=[], manga=[],
    err_rel='429: Too Many Requests',
    err_ep='Timeout',
    err_q='500: Internal Server Error',
    err_mg='Auth failed',
)

# 8. Overflow — "+N more" in all columns
_render('overflow',
    releases=[_release(f'Anime Release {i}', f'{i}d 0h') for i in range(1, 8)],
    episodes=[
        _episode(f'Long Running Show Episode Title {i}', f'{i*5} ep',
                 f'{i}d {i}h', watched=i*5, total=100)
        for i in range(1, 10)
    ],
    queue=[_queue(f'Queued Anime Title Number {i}', i*5, 24) for i in range(1, 10)],
    manga=[_manga(f'Manga Series {i}', i*10, 400, '+1 new') for i in range(1, 8)],
)

# 9. Col3 — queue fills column, no room for manga section
_render('col3_no_manga',
    releases=[],
    episodes=[_episode('Frieren', '4 ep', '1d 6h', watched=3, total=28)],
    queue=[_queue(f'Long Anime Title That Takes Space {i}', i*10, 100)
           for i in range(1, 8)],
    manga=[_manga('Berserk', 374, 400, '+2 new')],
)

print(f'\nSaved 9 images to {OUT_DIR}')
