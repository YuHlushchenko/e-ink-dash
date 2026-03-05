from PIL import Image
from screens.base_screen import BaseScreen
from components import year_progress, calendar, clock, art_panel


class Screen1(BaseScreen):
    def render(self) -> Image.Image:
        image = Image.new('L', (self.width, self.height), 255)
        year_progress.draw(image)
        calendar.draw(image)
        clock.draw(image)
        art_panel.draw(image)
        return image
