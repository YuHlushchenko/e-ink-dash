import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from renderer.base import Renderer
from screens.screen3 import Screen3

renderer = Renderer()
renderer.init()
renderer.clear()

screen = Screen3(renderer)
renderer.display(screen.render())
renderer.sleep()
