"""
Render the clock widget on the e-ink panel.

To freeze time, uncomment the MOCK_NOW block below.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

# ── Optional: uncomment and edit to freeze time ───────────────────────────────
# import config
# from datetime import datetime
# config.MOCK_NOW = datetime(2026, 3, 10, 14, 30)
# ─────────────────────────────────────────────────────────────────────────────

from PIL import Image
from renderer.base import Renderer
from components import clock

renderer = Renderer()
renderer.init()
renderer.clear()

image = Image.new('L', (renderer.width, renderer.height), 255)
clock.draw(image)

renderer.display(image)
renderer.sleep()
