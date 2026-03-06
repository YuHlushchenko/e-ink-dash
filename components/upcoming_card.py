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
GRAY = 160   # "aired but not watched" color


@lru_cache(maxsize=None)
def _font(path, size):
    return ImageFont.truetype(path, size)


def _truncate(draw_ctx, text, font, max_w):
    if draw_ctx.textlength(text, font=font) <= max_w:
        return text
    while text and draw_ctx.textlength(text + '...', font=font) > max_w:
        text = text[:-1]
    return text + '...'


def _draw_mixed(draw_ctx, x, y, segments, max_x, default_fill):
    for text, font, fill in segments:
        if x >= max_x:
            break
        draw_ctx.text((x, y), text, font=font, fill=fill)
        x += int(draw_ctx.textlength(text, font=font))
    return x


def draw(image, x, y, w,
         title,       # str
         ep_label,    # str: e.g. '9 ep' or 'FINAL'
         time_until,  # str: e.g. '4d 3h'
         final_date,  # str: e.g. 'Apr 28' or '∞'
         watched,     # int: episodes watched by user
         total,       # int: total episodes in season
         behind,      # int: aired but not yet watched
         highlight=False,  # black bg, white text
         ) -> int:
    """Draw an Upcoming Episodes card. Returns y_bottom."""
    draw_ctx = ImageDraw.Draw(image)
    font_reg  = _font(config.FONT_PATH,      FONT_SIZE)
    font_bold = _font(config.FONT_BOLD_PATH, FONT_SIZE)

    bg   = 0   if highlight else 255
    fg   = 255 if highlight else 0
    # progress bar colors
    bar_watched = 255 if highlight else 0       # watched: white on black bg, black on white bg
    bar_behind  = 80  if highlight else GRAY    # behind: dark gray on black, light gray on white
    bar_empty   = 0   if highlight else 255     # not aired: black on black bg, white on white bg

    inner_x = x + PAD
    max_x   = x + w - PAD

    lh = draw_ctx.textbbox((0, 0), 'Ag', font=font_reg)[3]
    card_h = PAD + lh + LINE_GAP + lh + BAR_GAP + BAR_H + PAD

    # Card background + border
    draw_ctx.rounded_rectangle(
        [x, y, x + w - 1, y + card_h - 1],
        radius=RADIUS, fill=bg, outline=fg,
    )

    line1_y = y + PAD
    line2_y = line1_y + lh + LINE_GAP

    # --- Line 1: title • ep_label ---
    ep_seg = [(' \u2022 ', font_reg, fg), (ep_label, font_bold, fg)]
    ep_w = sum(int(draw_ctx.textlength(t, font=f)) for t, f, _ in ep_seg)
    title_text = _truncate(draw_ctx, title, font_bold, (max_x - inner_x) - ep_w)
    _draw_mixed(draw_ctx, inner_x, line1_y, [
        (title_text, font_bold, fg),
        *ep_seg,
    ], max_x, fg)

    # --- Line 2: in TIME • Final DATE • WATCHED/TOTAL behind BEHIND ---
    _draw_mixed(draw_ctx, inner_x, line2_y, [
        ('in ',            font_reg,  fg),
        (time_until,       font_bold, fg),
        (' \u2022 Final ', font_reg,  fg),
        (final_date,       font_bold, fg),
        (' \u2022 ',           font_reg,  fg),
        (f'{watched}/{total}', font_bold, fg),
        (' \u2022 ',           font_reg,  fg),
        (f'+{behind}',         font_bold, fg),
    ], max_x, fg)

    # --- Progress bar ---
    bar_x = inner_x
    bar_y = y + card_h - PAD - BAR_H
    bar_w = w - 2 * PAD

    # Background (empty / not aired)
    draw_ctx.rounded_rectangle(
        [bar_x, bar_y, bar_x + bar_w - 1, bar_y + BAR_H - 1],
        radius=BAR_R, fill=bar_empty, outline=fg,
    )
    # Behind (aired, not watched)
    behind_w = int(bar_w * (watched + behind) / max(total, 1))
    if behind_w > 0:
        draw_ctx.rounded_rectangle(
            [bar_x, bar_y, bar_x + behind_w - 1, bar_y + BAR_H - 1],
            radius=BAR_R, fill=bar_behind,
        )
    # Watched
    watched_w = int(bar_w * watched / max(total, 1))
    if watched_w > 0:
        draw_ctx.rounded_rectangle(
            [bar_x, bar_y, bar_x + watched_w - 1, bar_y + BAR_H - 1],
            radius=BAR_R, fill=bar_watched,
        )

    return y + card_h
