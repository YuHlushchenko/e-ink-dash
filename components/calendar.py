import calendar as cal_module
import io
from datetime import date
from functools import lru_cache
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import config
import components.year_progress as _yp

ICONS_DIR = Path(__file__).parent.parent / 'assets' / 'icons'


@lru_cache(maxsize=None)
def _font(path: str, size: int):
    return ImageFont.truetype(path, size)


def draw(image, x=503, y=14, w=290, today=None):
    if today is None:
        today = date.today()

    draw_ctx = ImageDraw.Draw(image)

    font_title   = _font(config.FONT_BOLD_PATH, 22)
    font_bold    = _font(config.FONT_BOLD_PATH, 16)
    font_regular = _font(config.FONT_PATH,      16)

    HEADER_H     = 34
    HEADER_ROW_Y = y + 42   # day-of-week labels
    GRID_START_Y = y + 66   # first day row
    ICON_SIZE    = 18

    grid_bottom  = 480 - 14 - _yp.HEIGHT - 10
    MAX_ROWS     = 6
    ROW_H        = (grid_bottom - GRID_START_Y) // MAX_ROWS
    CELL_H       = ROW_H - 4

    # Column positions (7 equal-ish slots)
    col_starts = [x + round(w * i / 7) for i in range(7)] + [x + w]
    col_widths = [col_starts[i + 1] - col_starts[i] for i in range(7)]

    # --- Header bar ---
    draw_ctx.rounded_rectangle([x, y, x + w - 1, y + HEADER_H - 1], radius=4, fill=0)

    # Arrows
    arrow_y = y + (HEADER_H - ICON_SIZE) // 2
    _paste_arrow(image, x + 8,                  arrow_y, ICON_SIZE, left=True)
    _paste_arrow(image, x + w - 8 - ICON_SIZE,  arrow_y, ICON_SIZE, left=False)

    # Title
    title = today.strftime('%B %Y')
    draw_ctx.text((x + w // 2, y + HEADER_H // 2), title, font=font_title, fill=255, anchor='mm')

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


def _paste_arrow(image, x, y, size, left=True):
    try:
        import cairosvg
        name = 'arrow-left-rounded.svg' if left else 'arrow-right-rounded.svg'
        svg_bytes = (ICONS_DIR / name).read_bytes()
        png_bytes = cairosvg.svg2png(
            bytestring=svg_bytes,
            output_width=size, output_height=size,
            background_color='black',
        )
        icon = Image.open(io.BytesIO(png_bytes)).convert('L')
        image.paste(icon, (x, y))
    except Exception as e:
        print(f'[calendar] arrow icon error: {e}')
