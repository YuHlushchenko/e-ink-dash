"""
Render the loading screen once and display it on the e-ink panel.

To check a different dot count (0-3), edit DOTS below.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

DOTS = 0   # 0='Loading' 1='Loading.' 2='Loading..' 3='Loading...'

from renderer.base import Renderer
from screens.loading_screen import LoadingScreen

renderer = Renderer()
renderer.init()
renderer.clear()

renderer.display(LoadingScreen(renderer).render(DOTS))
renderer.sleep()
