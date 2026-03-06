"""Quick test: render starfield pixel art and display it on the e-ink panel."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from renderer.base import Renderer
from components.pixel_art import render_starfield

W, H = 200, 216

renderer = Renderer()
renderer.init()
renderer.clear()

img = render_starfield(W, H)
from PIL import Image
canvas = Image.new('L', (renderer.width, renderer.height), 255)
canvas.paste(img, (14, 50))
renderer.display(canvas)
renderer.sleep()
