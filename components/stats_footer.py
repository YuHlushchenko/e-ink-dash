from functools import lru_cache
from PIL import ImageDraw, ImageFont
import config
from utils.drawing import draw_gradient_bar

HEIGHT = 24
GRAD_H = 8
GRAD_R = 4
PAD = 14
GAP = 8


@lru_cache(maxsize=None)
def _font(path, size):
    return ImageFont.truetype(path, size)


def draw(image, y=None, stats: list = None):
    """
    Draw footer stats bar with gradient bars on both sides.

    stats — list of (label, value) tuples, e.g.:
        [('Watching: ', '12'), ('Planning: ', '3'), ...]
    Rendered as: label value • label value • ...
    """
    if y is None:
        y = 480 - PAD - HEIGHT
    if stats is None:
        stats = []

    draw_ctx = ImageDraw.Draw(image)
    font_reg  = _font(config.FONT_PATH,      13)
    font_bold = _font(config.FONT_BOLD_PATH, 13)

    # Build segments: [(text, font), ...]
    segments = []
    for i, (label, value) in enumerate(stats):
        if i > 0:
            segments.append((' \u2022 ', font_reg))
        segments.append((label, font_reg))
        segments.append((value, font_bold))

    total_w = sum(int(draw_ctx.textlength(t, font=f)) for t, f in segments)

    text_x = (800 - total_w) // 2
    text_y = y + (HEIGHT - _font(config.FONT_PATH, 13).size) // 2

    # Draw gradient bars
    bar_y = y + (HEIGHT - GRAD_H) // 2
    left_bar_w  = text_x - PAD - GAP
    right_bar_x = text_x + total_w + GAP
    right_bar_w = 800 - PAD - right_bar_x

    draw_gradient_bar(image, PAD, bar_y, left_bar_w,  GRAD_H, GRAD_R, reverse=False)
    draw_gradient_bar(image, right_bar_x, bar_y, right_bar_w, GRAD_H, GRAD_R, reverse=True)

    # Draw text segments
    x = text_x
    for text, font in segments:
        draw_ctx.text((x, text_y), text, font=font, fill=0)
        x += int(draw_ctx.textlength(text, font=font))
