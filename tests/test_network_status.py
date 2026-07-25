"""
art_panel notif bar wifi icon — screenshot test, no hardware, no network calls.

Status is mocked via monkeypatching utils.network_status.get_status (the cache-only
read the component calls). Covers all 3 states.

Output: tests/output/network_status_*.png

Run:
    python3 tests/test_network_status.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from PIL import Image
import utils.network_status as network_status

OUT_DIR = Path(__file__).parent / 'output'
OUT_DIR.mkdir(exist_ok=True)

from components import art_panel


def _render(label, status):
    network_status.get_status = lambda: status

    image = Image.new('L', (232, 56), 255)
    art_panel.draw_notif_bar(image, x=14, y=14, w=202)
    bw = image.convert('1', dither=Image.FLOYDSTEINBERG).convert('L')
    bw.save(OUT_DIR / f'network_status_{label}.png')
    print(f'  ✓  {label}')


_render('ok', 'ok')
_render('no_internet', 'no_internet')
_render('no_network', 'no_network')

print(f'\nSaved 3 images to {OUT_DIR}')
