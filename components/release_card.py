from functools import lru_cache
from PIL import ImageDraw, ImageFont
import config

PAD = 6
LINE_GAP = 4
RADIUS = 4
FONT_SIZE = 13


@lru_cache(maxsize=None)
def _font(path, size):
    return ImageFont.truetype(path, size)


def _truncate(draw_ctx, text, font, max_w):
    """Truncate text with '...' to fit within max_w pixels."""
    if draw_ctx.textlength(text, font=font) <= max_w:
        return text
    while text and draw_ctx.textlength(text + '...', font=font) > max_w:
        text = text[:-1]
    return text + '...'


def _draw_mixed(draw_ctx, x, y, segments, max_x):
    """Draw [(text, font), ...] segments left-to-right. Returns final x."""
    for text, font in segments:
        if x >= max_x:
            break
        draw_ctx.text((x, y), text, font=font, fill=0)
        x += int(draw_ctx.textlength(text, font=font))
    return x


def draw(image, x, y, w, title, eps_count, starts_in, final_ep) -> int:
    """
    Draw an Upcoming Releases card. Returns y_bottom.

    title      — show title (auto-truncated)
    eps_count  — total episodes (int)
    starts_in  — formatted time string, e.g. '11d 3h'
    final_ep   — final episode date string, e.g. 'Jun 28'
    """
    draw_ctx = ImageDraw.Draw(image)
    font_reg  = _font(config.FONT_PATH,      FONT_SIZE)
    font_bold = _font(config.FONT_BOLD_PATH, FONT_SIZE)

    inner_x = x + PAD
    inner_w = w - 2 * PAD

    # Measure line heights
    lh = draw_ctx.textbbox((0, 0), 'Ag', font=font_reg)[3]
    card_h = PAD + lh + LINE_GAP + lh + PAD

    # Card border
    draw_ctx.rounded_rectangle(
        [x, y, x + w - 1, y + card_h - 1],
        radius=RADIUS, fill=255, outline=0,
    )

    line1_y = y + PAD
    line2_y = line1_y + lh + LINE_GAP

    # --- Line 1: "Title... • N eps" ---
    eps_segments = [(' \u2022 ', font_reg), (str(eps_count), font_bold), (' eps', font_reg)]
    eps_w = sum(int(draw_ctx.textlength(t, font=f)) for t, f in eps_segments)
    title_max_w = inner_w - eps_w
    title_text = _truncate(draw_ctx, title, font_bold, title_max_w)

    _draw_mixed(draw_ctx, inner_x, line1_y, [
        (title_text, font_bold),
        *eps_segments,
    ], x + w - PAD)

    # --- Line 2: "Starts in Xd Yh • Final ep Jun 28" ---
    _draw_mixed(draw_ctx, inner_x, line2_y, [
        ('Starts in ',  font_reg),
        (starts_in,     font_bold),
        (' \u2022 Final ep ', font_reg),
        (final_ep,      font_bold),
    ], x + w - PAD)

    return y + card_h
