from datetime import date
from PIL import Image, ImageDraw, ImageFont
import config


def draw(image, x=0, y=206, today=None):
    if today is None:
        today = date.today()

    draw_ctx = ImageDraw.Draw(image)

    year = today.year
    year_start = date(year, 1, 1)
    year_end = date(year, 12, 31)
    total_days = (year_end - year_start).days + 1
    elapsed = (today - year_start).days       # 0-indexed: Jan 1 = 0
    days_left = total_days - elapsed - 1
    progress_pct = int((elapsed + 1) / total_days * 100)

    font_regular = ImageFont.truetype(config.FONT_PATH, 15)
    font_bold = ImageFont.truetype(config.FONT_BOLD_PATH, 15)
    font_title = ImageFont.truetype(config.FONT_BOLD_PATH, 20)
    font_label = ImageFont.truetype(config.FONT_PATH, 12)

    PADDING = 14

    # --- Title "2026 Progress" ---
    title = f'{year} Progress'
    title_bbox = draw_ctx.textbbox((0, 0), title, font=font_title)
    title_w = title_bbox[2] - title_bbox[0]
    title_x = x + (800 - title_w) // 2
    draw_ctx.text((title_x, y), title, font=font_title, fill=0)

    # --- Gradient bars flanking title (black outside → white inside) ---
    GRAD_H = 6
    title_h = title_bbox[3] - title_bbox[1]
    GRAD_Y = y + (title_h - GRAD_H) // 2
    GRAD_R = 4
    GAP = 8

    left_bar_x = x + PADDING
    left_bar_w = title_x - left_bar_x - GAP
    _draw_gradient_bar(image, left_bar_x, GRAD_Y, left_bar_w, GRAD_H, GRAD_R, reverse=False)

    right_bar_x = title_x + title_w + GAP
    right_bar_w = x + 800 - PADDING - right_bar_x
    _draw_gradient_bar(image, right_bar_x, GRAD_Y, right_bar_w, GRAD_H, GRAD_R, reverse=True)

    # --- GitHub-style year grid ---
    GRID_TOP = y + 56
    SQUARE = 12
    STEP = 14   # 12px square + 2px gap
    ROWS = 7

    first_dow = (year_start.weekday() + 1) % 7  # Sun=0
    total_positions = first_dow + total_days
    num_cols = (total_positions + ROWS - 1) // ROWS
    grid_width = (num_cols - 1) * STEP + SQUARE
    GRID_LEFT = x + (800 - grid_width) // 2
    GRID_RIGHT = GRID_LEFT + grid_width

    for day_idx in range(total_days):
        pos = first_dow + day_idx
        col = pos // ROWS
        row = pos % ROWS
        sq_x = GRID_LEFT + col * STEP
        sq_y = GRID_TOP + row * STEP
        if sq_x + SQUARE > GRID_RIGHT:
            break
        draw_ctx.rounded_rectangle(
            [sq_x, sq_y, sq_x + SQUARE - 1, sq_y + SQUARE - 1],
            radius=2,
            fill=0 if day_idx <= elapsed else 255,
            outline=0,
        )

    # --- Month labels ---
    MONTHS_Y = y + 35
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    for i, name in enumerate(months):
        first_of_month = (date(year, i + 1, 1) - year_start).days
        col = (first_dow + first_of_month) // ROWS
        draw_ctx.text((GRID_LEFT + col * STEP, MONTHS_Y), name, font=font_label, fill=0)

    # --- Stats line: "Progress 17%" ··· bar ··· "301 Days Left" ---
    STATS_Y = y + 162
    BAR_H = 12
    BAR_R = 4
    BAR_Y = STATS_Y + 2
    BAR_GAP = 8

    # Text widths
    label_left = 'Progress '
    num_left = f'{progress_pct}%'
    w_label_left = draw_ctx.textbbox((0, 0), label_left, font=font_regular)[2]
    w_num_left = draw_ctx.textbbox((0, 0), num_left, font=font_bold)[2]

    num_right = str(days_left)
    label_right = ' Days Left'
    w_num_right = draw_ctx.textbbox((0, 0), num_right, font=font_bold)[2]
    w_label_right = draw_ctx.textbbox((0, 0), label_right, font=font_regular)[2]

    # Draw left text
    draw_ctx.text((x + PADDING, STATS_Y), label_left, font=font_regular, fill=0)
    draw_ctx.text((x + PADDING + w_label_left, STATS_Y), num_left, font=font_bold, fill=0)

    # Draw right text
    right_text_x = x + 800 - PADDING - w_num_right - w_label_right
    draw_ctx.text((right_text_x, STATS_Y), num_right, font=font_bold, fill=0)
    draw_ctx.text((right_text_x + w_num_right, STATS_Y), label_right, font=font_regular, fill=0)

    # Progress bar (between texts)
    BAR_X = x + PADDING + w_label_left + w_num_left + BAR_GAP
    BAR_END = right_text_x - BAR_GAP
    BAR_W = BAR_END - BAR_X

    draw_ctx.rounded_rectangle([BAR_X, BAR_Y, BAR_END - 1, BAR_Y + BAR_H - 1],
                                radius=BAR_R, fill=255, outline=0)
    filled_w = max(BAR_R * 2, int(BAR_W * (elapsed + 1) / total_days))
    draw_ctx.rounded_rectangle([BAR_X, BAR_Y, BAR_X + filled_w - 1, BAR_Y + BAR_H - 1],
                                radius=BAR_R, fill=0)


def _draw_gradient_bar(image, x, y, w, h, radius, reverse=False):
    if w <= 0:
        return
    gradient = Image.new('L', (w, h))
    g_draw = ImageDraw.Draw(gradient)
    for i in range(w):
        value = int(i * 255 / max(w - 1, 1))
        if reverse:
            value = 255 - value
        g_draw.line([(i, 0), (i, h - 1)], fill=value)
    mask = Image.new('L', (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, w - 1, h - 1], radius=radius, fill=255)
    image.paste(gradient, (x, y), mask)
