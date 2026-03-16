"""
Screen 3 tests — run without hardware, output to tests/output/.

Cases:
  1. normal_render   — current random art scaled to 800x480 with dithering
  2. empty_fallback  — no arts available → black screen
  3. no_repeat       — pick_random() never returns the same path twice in a row
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from PIL import Image
from screens.screen3 import Screen3, ARTS_DIR

OUT_DIR = Path(__file__).parent / 'output'
OUT_DIR.mkdir(exist_ok=True)

class FakeRenderer:
    width  = 800
    height = 480

renderer = FakeRenderer()


def _save(image: Image.Image, name: str):
    bw = image.convert('1', dither=Image.FLOYDSTEINBERG).convert('L')
    path = OUT_DIR / f'screen3_{name}.png'
    bw.save(path)
    print(f'  ✓  {name:30s}  →  {path.name}')


# ── 1. Normal render ────────────────────────────────────────────────────────
arts = [f for p in ('*.jpg', '*.jpeg', '*.png') for f in ARTS_DIR.glob(p)]
if arts:
    screen = Screen3(renderer)
    _save(screen.render(), 'normal_render')
else:
    print('  –  normal_render                  SKIPPED (no arts in assets/arts/)')


# ── 2. Empty fallback ───────────────────────────────────────────────────────
screen_empty = Screen3.__new__(Screen3)
screen_empty.renderer = renderer
screen_empty.width    = renderer.width
screen_empty.height   = renderer.height
screen_empty._current_path = None

result = screen_empty.render()
assert result.size == (800, 480), 'fallback wrong size'
assert result.getextrema() == (0, 0), 'fallback should be pure black'
_save(result, 'empty_fallback')


# ── 3. No-repeat ────────────────────────────────────────────────────────────
if len(arts) >= 2:
    screen = Screen3(renderer)
    prev = screen._current_path
    repeated = False
    for _ in range(min(20, len(arts) * 2)):
        screen.pick_random()
        if screen._current_path == prev:
            repeated = True
            break
        prev = screen._current_path
    status = 'FAIL — same art repeated!' if repeated else 'OK'
    print(f'  ✓  no_repeat                       {status}')
elif len(arts) == 1:
    print('  –  no_repeat                       SKIPPED (only 1 art — repeat unavoidable)')
else:
    print('  –  no_repeat                       SKIPPED (no arts in assets/arts/)')


print(f'\nDone. Output: {OUT_DIR}')
