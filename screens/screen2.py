from PIL import Image
from screens.base_screen import BaseScreen


class Screen2(BaseScreen):
    def render(self) -> Image.Image:
        image = Image.new('L', (self.width, self.height), 255)
        # TODO: AniList + MangaDex
        return image
