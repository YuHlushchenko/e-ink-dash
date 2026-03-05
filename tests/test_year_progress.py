import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from PIL import Image
from renderer.base import Renderer
from components import year_progress

renderer = Renderer()
renderer.init()
renderer.clear()

image = Image.new('L', (renderer.width, renderer.height), 255)
year_progress.draw(image)

renderer.display(image)
renderer.sleep()
