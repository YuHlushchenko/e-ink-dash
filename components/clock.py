from datetime import datetime, timedelta
from functools import lru_cache
from PIL import ImageDraw, ImageFont
import config


@lru_cache(maxsize=None)
def _font(path: str, size: int):
    return ImageFont.truetype(path, size)


def draw(image, x=224, y=14, dt: datetime = None):
    """
    Draw the clock widget.
    dt — datetime to render (timezone-aware or naive). Defaults to real time via get_now().
    """
    if dt is None:
        from utils.time import get_now
        dt = get_now()

    draw_ctx = ImageDraw.Draw(image)

    W   = 263
    H   = 254
    PAD = 16

    font_regular = _font(config.FONT_PATH,      16)
    font_bold    = _font(config.FONT_BOLD_PATH, 16)
    font_time    = _font(config.FONT_BOLD_PATH, 40)
    font_small   = _font(config.FONT_PATH,      14)

    # --- Container ---
    draw_ctx.rounded_rectangle([x, y, x + W - 1, y + H - 1], radius=12, fill=255, outline=0)

    # --- "It's" ---
    draw_ctx.text((x + PAD, y + 24), "It's", font=font_small, fill=0)

    # --- Time (digits + am/pm separated to avoid kerning gap) ---
    time_num  = dt.strftime('%I:%M')
    time_ampm = dt.strftime('%p').lower()
    AMPM_GAP  = 6

    nb = draw_ctx.textbbox((0, 0), time_num,  font=font_time)
    ab = draw_ctx.textbbox((0, 0), time_ampm, font=font_time)
    total_w = (nb[2] - nb[0]) + AMPM_GAP + (ab[2] - ab[0])

    time_y  = y + 54
    start_x = x + (W - total_w) // 2
    AMPM_DROP = 10
    draw_ctx.text((start_x - nb[0], time_y - nb[1]),
                  time_num, font=font_time, fill=0)
    draw_ctx.text((start_x + (nb[2] - nb[0]) + AMPM_GAP - ab[0],
                   time_y - ab[1] + AMPM_DROP),
                  time_ampm, font=font_time, fill=0)

    # --- "right now" (right-aligned) ---
    rn   = 'right now'
    rn_b = draw_ctx.textbbox((0, 0), rn, font=font_small)
    draw_ctx.text((x + W - PAD - (rn_b[2] - rn_b[0]), y + 108), rn, font=font_small, fill=0)

    # --- Bullets ---
    bullets = _compute_bullets(dt)

    right_limit = x + W - PAD
    cur_y = y + 150
    bx    = x + PAD
    dot   = '\u2022 '
    dot_w = draw_ctx.textbbox((0, 0), dot, font=font_regular)[2]

    for label, value in bullets:
        draw_ctx.text((bx, cur_y), dot, font=font_regular, fill=0)

        label_w = draw_ctx.textbbox((0, 0), label, font=font_regular)[2]
        draw_ctx.text((bx + dot_w,  cur_y), label, font=font_regular, fill=0)

        val_x  = bx + dot_w + label_w
        val_b = draw_ctx.textbbox((0, 0), value, font=font_bold)
        if val_x + (val_b[2] - val_b[0]) <= right_limit:
            draw_ctx.text((val_x, cur_y), value, font=font_bold, fill=0)
            cur_y += 26
        else:
            cur_y += 26
            draw_ctx.text((bx + dot_w, cur_y), value, font=font_bold, fill=0)
            cur_y += 26


# ---------------------------------------------------------------------------
# Bullet computation

def _compute_bullets(dt: datetime) -> list:
    return [
        _bullet_work(dt),
        _bullet_day_ends(dt),
        _bullet_weekend(dt),
    ]


def _bullet_work(dt: datetime) -> tuple:
    """'Work ends in X' during work hours on weekdays, else 'Work starts in X'."""
    wd   = dt.weekday()             # Mon=0 … Fri=4, Sat=5, Sun=6
    cur  = dt.hour * 60 + dt.minute
    wst  = config.WORK_START * 60   # work start in minutes since midnight
    wend = config.WORK_END   * 60   # work end   in minutes since midnight

    if wd < 5 and wst <= cur < wend:
        return ('Work ends in ', _fmt(wend - cur))

    if wd < 5 and cur < wst:
        return ('Work starts in ', _fmt(wst - cur))

    # After work on a weekday, or weekend — find next workday start
    if wd == 4:    # Friday after work → Monday
        days_ahead = 3
    elif wd == 5:  # Saturday → Monday
        days_ahead = 2
    elif wd == 6:  # Sunday → Monday
        days_ahead = 1
    else:          # Mon–Thu after work → tomorrow
        days_ahead = 1
    next_start = _midnight_of(dt) + timedelta(days=days_ahead) + timedelta(minutes=wst)
    return ('Work starts in ', _fmt(_mins_until(dt, next_start)))


def _bullet_day_ends(dt: datetime) -> tuple:
    """'Day ends in X' — time until midnight (00:00 next day)."""
    midnight = _midnight_of(dt) + timedelta(days=1)
    return ('Day ends in ', _fmt(_mins_until(dt, midnight)))


def _bullet_weekend(dt: datetime) -> tuple:
    """
    Weekday  → 'Weekend in X'    — time until Saturday 00:00.
    Weekend  → 'Weekend ends in X' — time until Monday 00:00.
    """
    wd = dt.weekday()   # Mon=0 … Sat=5, Sun=6

    if wd >= 5:   # Saturday or Sunday
        days_to_monday = 7 - wd   # Sat→2, Sun→1
        target = _midnight_of(dt) + timedelta(days=days_to_monday)
        return ('Weekend ends in ', _fmt(_mins_until(dt, target)))
    else:
        days_to_saturday = 5 - wd   # Mon→5, Tue→4, … Fri→1
        target = _midnight_of(dt) + timedelta(days=days_to_saturday)
        return ('Weekend in ', _fmt(_mins_until(dt, target)))


# ---------------------------------------------------------------------------
# Helpers

def _midnight_of(dt: datetime) -> datetime:
    """Return 00:00:00 of the same day (preserves tzinfo)."""
    return dt.replace(hour=0, minute=0, second=0, microsecond=0)


def _mins_until(dt: datetime, target: datetime) -> int:
    """Minutes from dt (truncated to minute) until target."""
    delta = target - dt.replace(second=0, microsecond=0)
    return max(0, int(delta.total_seconds() / 60))


def _fmt(total_minutes: int) -> str:
    """'Xd Yh' when >= 1 day, else 'Xh Ym'."""
    days    = total_minutes // (60 * 24)
    hours   = (total_minutes % (60 * 24)) // 60
    minutes = total_minutes % 60
    if days >= 1:
        return f'{days}d {hours}h'
    return f'{hours}h {minutes}m'
