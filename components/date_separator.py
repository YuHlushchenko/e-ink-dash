from datetime import date as Date
from functools import lru_cache
from PIL import ImageDraw, ImageFont
import config

HEIGHT = 18


@lru_cache(maxsize=None)
def _font(path, size):
    return ImageFont.truetype(path, size)


def draw(image, x, y, w, date: Date) -> int:
    """Draw date label + horizontal line to the right. Returns y_bottom."""
    draw_ctx = ImageDraw.Draw(image)
    font = _font(config.FONT_PATH, 14)

    label = date.strftime('%b %-d, %Y • %a')
    bbox = draw_ctx.textbbox((0, 0), label, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    text_top = y + (HEIGHT - text_h) // 2
    text_y = text_top - bbox[1]
    draw_ctx.text((x, text_y), label, font=font, fill=0)

    line_x = x + text_w + 6
    line_y = text_top + text_h // 2   # aligned to visual center of text
    draw_ctx.line([(line_x, line_y), (x + w, line_y)], fill=0, width=1)

    return y + HEIGHT
