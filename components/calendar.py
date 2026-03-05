import calendar as cal_module
from datetime import date
from PIL import Image, ImageDraw, ImageFont
import config


def draw(image, x=521, y=14, w=265, today=None):
    if today is None:
        today = date.today()

    draw_ctx = ImageDraw.Draw(image)

    font_title  = ImageFont.truetype(config.FONT_BOLD_PATH, 20)
    font_bold   = ImageFont.truetype(config.FONT_BOLD_PATH, 14)
    font_regular = ImageFont.truetype(config.FONT_PATH, 14)

    HEADER_H     = 26
    HEADER_ROW_Y = y + 32   # day-of-week labels
    GRID_START_Y = y + 53   # first day row
    ICON_SIZE    = 16

    # Fill down to year_progress top (480 - 14 - 176 = 290) with 10px gap
    import components.year_progress as _yp
    grid_bottom  = 480 - 14 - _yp.HEIGHT - 50
    MAX_ROWS     = 6
    ROW_H        = (grid_bottom - GRID_START_Y) // MAX_ROWS
    CELL_H       = ROW_H - 6

    # Column positions (7 equal-ish slots)
    col_starts = [x + round(w * i / 7) for i in range(7)] + [x + w]
    col_widths = [col_starts[i + 1] - col_starts[i] for i in range(7)]

    # --- Header bar ---
    draw_ctx.rounded_rectangle([x, y, x + w - 1, y + HEADER_H - 1], radius=4, fill=0)

    # Arrows
    arrow_y = y + (HEADER_H - ICON_SIZE) // 2
    _draw_chevron(draw_ctx, x + 8, arrow_y, ICON_SIZE, left=True)
    _draw_chevron(draw_ctx, x + w - 8 - ICON_SIZE, arrow_y, ICON_SIZE, left=False)

    # Title
    title = today.strftime('%B %Y')
    tb = draw_ctx.textbbox((0, 0), title, font=font_title)
    title_x = x + (w - (tb[2] - tb[0])) // 2
    title_y = y + (HEADER_H - (tb[3] - tb[1])) // 2
    draw_ctx.text((title_x, title_y), title, font=font_title, fill=255)

    # --- Day-of-week headers ---
    headers = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
    for i, hdr in enumerate(headers):
        font = font_bold if i in (0, 6) else font_regular
        hb = draw_ctx.textbbox((0, 0), hdr, font=font)
        hdr_x = col_starts[i] + (col_widths[i] - (hb[2] - hb[0])) // 2
        draw_ctx.text((hdr_x, HEADER_ROW_Y), hdr, font=font, fill=0)

    # --- Day grid ---
    cal = cal_module.Calendar(firstweekday=6)  # Sunday first
    weeks = cal.monthdayscalendar(today.year, today.month)

    for week_idx, week in enumerate(weeks):
        for dow, day in enumerate(week):
            if day == 0:
                continue

            font = font_bold if dow in (0, 6) else font_regular
            day_str = str(day)
            db = draw_ctx.textbbox((0, 0), day_str, font=font)
            dw = db[2] - db[0]
            dh = db[3] - db[1]

            cell_x = col_starts[dow]
            cell_y = GRID_START_Y + week_idx * ROW_H
            text_x = cell_x + (col_widths[dow] - dw) // 2 - db[0]
            text_y = cell_y + (CELL_H - dh) // 2 - db[1]

            if day == today.day:
                draw_ctx.rounded_rectangle(
                    [cell_x, cell_y, cell_x + col_widths[dow] - 1, cell_y + CELL_H - 1],
                    radius=4, fill=0,
                )
                draw_ctx.text((text_x, text_y), day_str, font=font, fill=255)
            else:
                draw_ctx.text((text_x, text_y), day_str, font=font, fill=0)


def _draw_chevron(draw_ctx, x, y, size, left=True):
    cx = x + size // 2
    cy = y + size // 2
    offset = size // 3
    if left:
        pts = [(cx + offset // 2, cy - offset), (cx - offset // 2, cy), (cx + offset // 2, cy + offset)]
    else:
        pts = [(cx - offset // 2, cy - offset), (cx + offset // 2, cy), (cx - offset // 2, cy + offset)]
    draw_ctx.line(pts, fill=255, width=2)
