"""
Loading screen preview — no hardware, no API calls needed.

Renders each dot-count variant to tests/output/ (gitignored) so the
centering and the fixed partial-refresh text_region() box can be
checked visually.

Run:
    python3 tests/test_loading_screen.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from PIL import Image, ImageDraw
from screens.loading_screen import LoadingScreen

OUT_DIR = Path(__file__).parent / 'output'
OUT_DIR.mkdir(exist_ok=True)


class FakeRenderer:
    width = 800
    height = 480


renderer = FakeRenderer()
screen = LoadingScreen(renderer)
region = screen.text_region()
print(f'text_region() = {region}')
assert region[0] % 8 == 0 and region[2] % 8 == 0, 'x-coords must be multiples of 8'

for dots in range(4):
    img = screen.render(dots)

    # Draw the text_region box for visual inspection
    preview = img.convert('RGB')
    ImageDraw.Draw(preview).rectangle(region, outline=(255, 0, 0))

    bw = img.convert('1', dither=Image.FLOYDSTEINBERG).convert('L')
    bw.save(OUT_DIR / f'loading_dots_{dots}.png')
    preview.save(OUT_DIR / f'loading_dots_{dots}_region.png')
    print(f'  ✓  dots={dots}')

print(f'\nSaved to {OUT_DIR}')
