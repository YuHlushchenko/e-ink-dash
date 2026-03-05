from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import config


DEFAULT_BULLETS = [
    ('Work ends in ', '5h 1m'),
    ('Day ends in ', '10h 1m'),
    ('Weekend in ', '7d 10h'),
]


def format_duration(total_minutes):
    """Returns 'Xd Yh' if >= 1 day, else 'Xh Ym'."""
    days = total_minutes // (60 * 24)
    hours = (total_minutes % (60 * 24)) // 60
    minutes = total_minutes % 60
    if days >= 1:
        return f'{days}d {hours}h'
    return f'{hours}h {minutes}m'


def draw(image, x=228, y=14, bullets=None):
    now = datetime.now()
    draw_ctx = ImageDraw.Draw(image)

    W = 263
    H = 254
    PAD = 16

    font_regular = ImageFont.truetype(config.FONT_PATH, 16)
    font_bold    = ImageFont.truetype(config.FONT_BOLD_PATH, 16)
    font_time    = ImageFont.truetype(config.FONT_BOLD_PATH, 40)
    font_small   = ImageFont.truetype(config.FONT_PATH, 14)

    # --- Container ---
    draw_ctx.rounded_rectangle([x, y, x + W - 1, y + H - 1], radius=12, fill=255, outline=0)

    # --- "It's" ---
    draw_ctx.text((x + PAD, y + 24), "It's", font=font_small, fill=0)

    # --- Time: render "07:43" and "pm" separately to avoid wide monospace space ---
    time_num  = now.strftime('%I:%M')          # "07:43"
    time_ampm = now.strftime('%p').lower()     # "pm"
    AMPM_GAP  = 6

    nb = draw_ctx.textbbox((0, 0), time_num,  font=font_time)
    ab = draw_ctx.textbbox((0, 0), time_ampm, font=font_time)
    total_w = (nb[2] - nb[0]) + AMPM_GAP + (ab[2] - ab[0])

    time_y = y + 54
    start_x = x + (W - total_w) // 2
    AMPM_DROP = 10
    draw_ctx.text((start_x - nb[0], time_y - nb[1]), time_num,  font=font_time, fill=0)
    draw_ctx.text((start_x + (nb[2] - nb[0]) + AMPM_GAP - ab[0], time_y - ab[1] + AMPM_DROP), time_ampm, font=font_time, fill=0)

    # --- "right now" (right-aligned) ---
    rn = 'right now'
    rn_b = draw_ctx.textbbox((0, 0), rn, font=font_small)
    draw_ctx.text((x + W - PAD - (rn_b[2] - rn_b[0]), y + 108), rn, font=font_small, fill=0)

    # --- Bullets ---
    if bullets is None:
        bullets = DEFAULT_BULLETS

    right_limit = x + W - PAD
    cur_y = y + 150

    for label, value in bullets:
        bx = x + PAD

        dot = '\u2022 '
        dot_w = draw_ctx.textbbox((0, 0), dot, font=font_regular)[2]
        draw_ctx.text((bx, cur_y), dot, font=font_regular, fill=0)

        label_w = draw_ctx.textbbox((0, 0), label, font=font_regular)[2]
        draw_ctx.text((bx + dot_w, cur_y), label, font=font_regular, fill=0)

        val_x = bx + dot_w + label_w
        val_b = draw_ctx.textbbox((0, 0), value, font=font_bold)
        if val_x + (val_b[2] - val_b[0]) <= right_limit:
            draw_ctx.text((val_x, cur_y), value, font=font_bold, fill=0)
            cur_y += 26
        else:
            cur_y += 26
            draw_ctx.text((bx + dot_w, cur_y), value, font=font_bold, fill=0)
            cur_y += 26
