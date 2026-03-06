from functools import lru_cache
from PIL import ImageDraw, ImageFont
import config

PAD = 6
LINE_GAP = 4
BAR_GAP = 5
BAR_H = 6
BAR_R = 3
RADIUS = 4
FONT_SIZE = 13


@lru_cache(maxsize=None)
def _font(path, size):
    return ImageFont.truetype(path, size)


def draw(image, x, y, w, title, current_ch, total_ch, status) -> int:
    """
    Draw a Manga Updates card. Returns y_bottom.

    title       — manga title
    current_ch  — last chapter read
    total_ch    — total chapters released
    status      — status string, e.g. 'New chapter available'
    """
    draw_ctx = ImageDraw.Draw(image)
    font_reg  = _font(config.FONT_PATH,      FONT_SIZE)
    font_bold = _font(config.FONT_BOLD_PATH, FONT_SIZE)

    inner_x = x + PAD
    max_x   = x + w - PAD

    lh = draw_ctx.textbbox((0, 0), 'Ag', font=font_reg)[3]
    card_h = PAD + lh + LINE_GAP + lh + BAR_GAP + BAR_H + PAD

    # Card border
    draw_ctx.rounded_rectangle(
        [x, y, x + w - 1, y + card_h - 1],
        radius=RADIUS, fill=255, outline=0,
    )

    line1_y = y + PAD
    line2_y = line1_y + lh + LINE_GAP

    # --- Line 1: title ---
    title_text = title
    while draw_ctx.textlength(title_text, font=font_bold) > (max_x - inner_x) and title_text:
        title_text = title_text[:-1]
    if title_text != title:
        title_text = title_text[:-3] + '...'
    draw_ctx.text((inner_x, line1_y), title_text, font=font_bold, fill=0)

    # --- Line 2: Ch current/total • status ---
    segments = [
        ('Ch ',                       font_reg),
        (f'{current_ch}/{total_ch}',  font_bold),
        (f' \u2022 {status}',         font_reg),
    ]
    x_cur = inner_x
    for text, font in segments:
        if x_cur >= max_x:
            break
        draw_ctx.text((x_cur, line2_y), text, font=font, fill=0)
        x_cur += int(draw_ctx.textlength(text, font=font))

    # --- Progress bar (chapters read / total) ---
    bar_x = inner_x
    bar_y = y + card_h - PAD - BAR_H
    bar_w = w - 2 * PAD

    draw_ctx.rounded_rectangle(
        [bar_x, bar_y, bar_x + bar_w - 1, bar_y + BAR_H - 1],
        radius=BAR_R, fill=255, outline=0,
    )
    read_w = int(bar_w * current_ch / max(total_ch, 1))
    if read_w > 0:
        draw_ctx.rounded_rectangle(
            [bar_x, bar_y, bar_x + read_w - 1, bar_y + BAR_H - 1],
            radius=BAR_R, fill=0,
        )

    return y + card_h
