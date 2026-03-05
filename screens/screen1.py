from PIL import Image
from screens.base_screen import BaseScreen


class Screen1(BaseScreen):
    def render(self) -> Image.Image:
        image = Image.new('L', (self.width, self.height), 255)
        # TODO: clock, calendar, year progress, anime art
        return image
