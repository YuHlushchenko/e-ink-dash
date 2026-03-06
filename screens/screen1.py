from datetime import datetime
from PIL import Image
from screens.base_screen import BaseScreen
from components import year_progress, calendar, clock, art_panel


class Screen1(BaseScreen):
    def render(self, dt: datetime = None) -> Image.Image:
        if dt is None:
            from utils.time import get_now
            dt = get_now()

        image = Image.new('L', (self.width, self.height), 255)
        today = dt.date()

        year_progress.draw(image, today=today)
        calendar.draw(image, today=today)
        clock.draw(image, dt=dt)
        art_panel.draw(image)
        return image
