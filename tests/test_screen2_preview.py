"""
Screen 2 hardware preview — renders screen2 on the real e-ink display.

Reads live data from AniList + MangaDex cache (no cache invalidation).

Run:
    python3 tests/test_screen2_preview.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from renderer.base import Renderer
from screens.screen2 import Screen2

renderer = Renderer()
screen   = Screen2(renderer)

print('Rendering Screen 2...')
image = screen.render()
renderer.display(image)
renderer.sleep()
print('Done.')
