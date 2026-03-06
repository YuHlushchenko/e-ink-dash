import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from renderer.base import Renderer
from screens.screen2 import Screen2

renderer = Renderer()
renderer.init()
renderer.clear()

renderer.display(Screen2(renderer).render())
renderer.sleep()
