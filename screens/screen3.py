import random
from pathlib import Path
from PIL import Image, ImageOps
from screens.base_screen import BaseScreen


ARTS_DIR = Path(__file__).parent.parent / 'assets' / 'arts'
SUPPORTED = ('*.jpg', '*.jpeg', '*.png')


class Screen3(BaseScreen):
    def __init__(self, renderer):
        super().__init__(renderer)
        self._current_path = None
        self.pick_random()

    def pick_random(self):
        arts = [f for pattern in SUPPORTED for f in ARTS_DIR.glob(pattern)]
        if arts:
            self._current_path = random.choice(arts)

    def render(self) -> Image.Image:
        if not self._current_path or not self._current_path.exists():
            return Image.new('L', (self.width, self.height), 0)

        image = Image.open(self._current_path).convert('L')
        image = ImageOps.fit(image, (self.width, self.height), method=Image.LANCZOS)
        return image
