"""
github_contribution.py screenshot tests — no hardware, no API calls.

Data is mocked via monkeypatching api.github.get_contributions (the cache-only read
the component calls). Covers: a fully populated trailing-365-day window, no data yet
(cold start / persistent fetch error — same fallback path, see api/github.py), and a
populated window with a few individual missing days (partial fetch gaps).

Output: tests/output/github_contribution_*.png

Run:
    python3 tests/test_github_contribution_screenshots.py
"""
import sys
from datetime import date, timedelta
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from PIL import Image
import api.github as github_api

OUT_DIR = Path(__file__).parent / 'output'
OUT_DIR.mkdir(exist_ok=True)

from components import github_contribution

TODAY = date(2026, 7, 12)
WINDOW_DAYS = 365
WINDOW_START = TODAY - timedelta(days=WINDOW_DAYS - 1)

LEVELS = ['NONE', 'FIRST_QUARTILE', 'SECOND_QUARTILE', 'THIRD_QUARTILE', 'FOURTH_QUARTILE']


def _render(label, contributions):
    github_api.get_contributions = lambda: (contributions, None)

    image = Image.new('L', (800, 480), 255)
    github_contribution.draw(image, today=TODAY)
    bw = image.convert('1', dither=Image.FLOYDSTEINBERG).convert('L')
    bw.save(OUT_DIR / f'github_contribution_{label}.png')
    print(f'  ✓  {label}')


# 1. Typical populated window — cycles through all 5 levels for visual variety
days = {
    (WINDOW_START + timedelta(days=i)).isoformat(): LEVELS[i % len(LEVELS)]
    for i in range(WINDOW_DAYS)
}
_render('typical', {'total': sum(1 for lv in days.values() if lv != 'NONE'), 'days': days})

# 2. No data at all — cold start or a fetch that has never once succeeded.
# Every day in the window must fall back to white, not crash.
_render('no_data', None)

# 3. Populated window with a few individual days missing (partial fetch gaps) —
# those specific squares must fall back to white even though the day is in-window.
partial_days = dict(days)
for i in (0, 10, WINDOW_DAYS // 2, WINDOW_DAYS - 1):
    partial_days.pop((WINDOW_START + timedelta(days=i)).isoformat(), None)
_render('partial_gaps', {'total': sum(1 for lv in partial_days.values() if lv != 'NONE'),
                          'days': partial_days})

print(f'\nSaved 3 images to {OUT_DIR}')
