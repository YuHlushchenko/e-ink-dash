"""
Render screen1 for various edge-case dates and save as PNG files.
Run on the Pi (or locally if waveshare_epd is mocked):

    python3 tests/test_dates.py

Output: tests/output/date_*.png
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime
from PIL import Image
import config

OUT_DIR = Path(__file__).parent / 'output'
OUT_DIR.mkdir(exist_ok=True)

# Patch renderer so we can run without actual hardware
class FakeRenderer:
    width  = 800
    height = 480

from screens.screen1 import Screen1
renderer = FakeRenderer()
screen   = Screen1(renderer)

CASES = [
    # (label,                          datetime)
    ('weekday_during_work',             datetime(2026, 3, 10, 14, 30)),   # Mon 14:30 — work
    ('weekday_before_work',             datetime(2026, 3, 10,  8,  0)),   # Mon 08:00 — before work
    ('weekday_after_work',              datetime(2026, 3, 10, 20,  0)),   # Mon 20:00 — after work
    ('friday_last_hour_of_work',        datetime(2026, 3, 13, 18, 45)),   # Fri 18:45
    ('friday_evening',                  datetime(2026, 3, 13, 21,  0)),   # Fri 21:00 — weekend starts
    ('saturday_morning',                datetime(2026, 3, 14, 10,  0)),   # Sat 10:00 — weekend
    ('sunday_late_night',               datetime(2026, 3, 15, 23, 30)),   # Sun 23:30 — weekend ends soon
    ('new_year_eve',                    datetime(2025, 12, 31, 23, 58)),  # Dec 31 23:58
    ('new_year_day',                    datetime(2026,  1,  1,  0,  1)),  # Jan 1 00:01
    ('leap_year_feb29',                 datetime(2028,  2, 29, 12,  0)),  # leap year
    ('leap_year_last_day',              datetime(2028, 12, 31, 23, 59)),  # leap year end
    ('midnight_transition',             datetime(2026,  3, 10, 23, 59)),  # 1 min before midnight
    ('long_weekend_bullet',             datetime(2026,  3,  9,  9,  0)),  # Mon 09:00 — "Weekend in 5d Xh"
    # Weekend work bullet edge cases
    ('friday_during_work',              datetime(2026,  3, 13, 15,  0)),  # Fri 15:00 — "Work ends in 4h 0m"
    ('friday_after_work',               datetime(2026,  3, 13, 20,  0)),  # Fri 20:00 — "Work starts in 2d Xh" (Mon)
    ('saturday_midday',                 datetime(2026,  3, 14, 12,  0)),  # Sat 12:00 — "Work starts in 1d Xh" (Mon)
    ('sunday_morning',                  datetime(2026,  3, 15,  9,  0)),  # Sun 09:00 — "Work starts in Xh Ym" (Mon)
    ('sunday_evening',                  datetime(2026,  3, 15, 22,  0)),  # Sun 22:00 — "Work starts in 12h 0m"
    ('monday_before_work',              datetime(2026,  3, 16,  9, 30)),  # Mon 09:30 — "Work starts in 0h 30m"
    ('thursday_after_work',             datetime(2026,  3, 12, 21,  0)),  # Thu 21:00 — "Work starts in Xh Ym" (Fri)
]

for label, dt in CASES:
    config.MOCK_NOW = dt
    image = screen.render()

    # Dither to B&W (mimics e-ink) then back to L for PNG
    bw = image.convert('1', dither=Image.FLOYDSTEINBERG).convert('L')
    out_path = OUT_DIR / f'date_{label}.png'
    bw.save(out_path)
    print(f'  ✓  {label:40s}  →  {out_path.name}')

config.MOCK_NOW = None
print(f'\nSaved {len(CASES)} images to {OUT_DIR}')
