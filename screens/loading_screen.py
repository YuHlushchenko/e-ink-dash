from functools import lru_cache
from PIL import Image, ImageDraw, ImageFont
from screens.base_screen import BaseScreen
import config

TEXT_SIZE = 32
PAD = 24   # padding around text inside the partial-refresh region


@lru_cache(maxsize=None)
def _font(path, size):
    return ImageFont.truetype(path, size)


class LoadingScreen(BaseScreen):
    def render(self, dots: int = 0) -> Image.Image:
        image = Image.new('L', (self.width, self.height), 255)
        draw_ctx = ImageDraw.Draw(image)
        text = 'Loading' + '.' * dots
        draw_ctx.text(
            (self.width // 2, self.height // 2), text,
            font=_font(config.FONT_BOLD_PATH, TEXT_SIZE), fill=0, anchor='mm',
        )
        return image

    def text_region(self) -> tuple:
        """Fixed partial-refresh box big enough for the longest dot variant,
        x-coords rounded outward to multiples of 8 (hardware alignment)."""
        return self._text_region_cached(self.width, self.height)

    @staticmethod
    @lru_cache(maxsize=None)
    def _text_region_cached(width, height):
        font = _font(config.FONT_BOLD_PATH, TEXT_SIZE)
        dummy = Image.new('L', (1, 1))
        bbox = ImageDraw.Draw(dummy).textbbox((width // 2, height // 2), 'Loading...', font=font, anchor='mm')
        x0, y0, x1, y1 = bbox
        x0 -= PAD
        y0 -= PAD
        x1 += PAD
        y1 += PAD
        x0 -= x0 % 8            # round down to multiple of 8
        x1 += (8 - x1 % 8) % 8  # round up to multiple of 8
        return (x0, y0, x1, y1)
