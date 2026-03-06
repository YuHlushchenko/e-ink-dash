from functools import lru_cache
from PIL import ImageDraw, ImageFont
import config

SECTION_H = 26


@lru_cache(maxsize=None)
def _font(path, size):
    return ImageFont.truetype(path, size)


def draw(image, x, y, w, title) -> int:
    """Draw section header. Returns y_bottom."""
    draw_ctx = ImageDraw.Draw(image)
    draw_ctx.rounded_rectangle(
        [x, y, x + w - 1, y + SECTION_H - 1],
        radius=4, fill=0,
    )
    draw_ctx.text(
        (x + w // 2, y + SECTION_H // 2),
        title,
        font=_font(config.FONT_BOLD_PATH, 14),
        fill=255,
        anchor='mm',
    )
    return y + SECTION_H
